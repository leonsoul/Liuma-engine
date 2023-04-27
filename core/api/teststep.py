import datetime
from time import sleep
from requests import request, Session
from copy import deepcopy
import json

from core.assertion import LMAssert
from lm.lm_log import DebugLogger
from tools.alltuu.Signature import Signature
from tools.utils.utils import extract, ExtractValueError, url_join
from urllib.parse import urlencode

REQUEST_CNAME_MAP = {
    'headers': '请求头',
    'proxies': '代理',
    'cookies': 'cookies',
    'params': '查询参数',
    'data': '请求体',
    'json': '请求体',
    'files': '上传文件'
}


class ApiTestStep:

    def __init__(self, test, session, collector, context, params):
        self.session = session
        self.collector = collector
        self.context = context
        self.params = params    # 公参
        self.test = test
        self.status_code = None
        self.response_headers = None
        self.response_content = None
        self.response_content_bytes = None
        self.response_cookies = None
        self.assert_result = None

    def execute(self):
        """测试执行"""
        try:
            self.test.debugLog('[{}][{}]接口执行开始'.format(self.collector.apiId, self.collector.apiName))
            request_log = '【请求信息】:<br>'
            request_log += '{} {}<br>'.format(self.collector.method, url_join(self.collector.url, self.collector.path))
            for key, value in self.collector.others.items():
                if value is not None:
                    c_key = REQUEST_CNAME_MAP[key] if key in REQUEST_CNAME_MAP else key
                    if key == 'files':
                        if isinstance(value, dict):
                            request_log += '{}: {}<br>'.format(c_key,
                                                               ["文件长度%s: %s" % (k, len(v)) for k, v in value.items()])
                        if isinstance(value, list):
                            request_log += '{}: {}<br>'.format(c_key, [i[1][0] for i in value])
                    else:
                        request_log += '{}: {}<br>'.format(c_key, log_msg(value))
            # 如果是x-www-form-urlencoded 格式，字段中有使用list或dict会报错，但是我们在系统中都会使用字符串代替，所以这段代码先注释掉了
            self.test.debugLog(request_log[:-4])
            # if self.collector.body_type == "form-urlencoded" and 'data' in self.collector.others:
            #     self.collector.others['data'] = urlencode(self.collector.others['data'])
            # if self.collector.body_type in ("text", "xml", "html") and 'data' in self.collector.others:
            #     self.collector.others['data'] = self.collector.others['data'].encode("utf-8")
            if 'files' in self.collector.others and self.collector.others['files'] is not None:
                self.pop_content_type()
            url = url_join(self.collector.url, self.collector.path)

            # 接口前置处理加密 --alltuu
            if self.collector.controller['encryption'].lower() == "setting":
                args_map = {}
                # 这里的签名有些问题
                if self.collector.others['params'] is not None:
                    args_map.update(self.collector.others['params'])
                    url += '/' + Signature().concatenating_url(self.collector.others['params'])
                    self.collector.others['params'] = None
                # 有两个选择，一个是在转义之前保存一分数据，另外一种是单独解密出来
                if 'data' in self.collector.others:
                    # if self.collector.body_type == "form-urlencoded":
                    #     args_map.update(Signature().decode_url(self.collector.others['data']))
                    # else:
                    args_map.update(self.collector.others['data'])
                # 只是简单的加密
                signature_string, signature = Signature().sign_url_v4(self.collector.controller['token'], args_map, no_sign_date=self.collector.private['no_sign_data'],source=self.collector.controller['From'])
                url = url + '/' + 'v' + signature_string

            elif self.collector.controller['encryption'].lower() == "crm":
                signature_string, signature = Signature().sign_url_v4(self.collector.controller['token'],
                                                                      self.collector.others['data'], no_sign_date=self.collector.private['no_sign_data'],source=self.collector.controller['From'])
                self.collector.others['data'].updata({signature: signature})
            elif self.collector.controller['encryption'].lower() == "live":
                args_map = {}
                if self.collector.others['params'] is not None:
                    args_map.update(self.collector.others['params'])
                    # 对url进行加密
                    url = self.collector.url + Signature().sign_url_v4c(self.collector.path, args_map)
            # 前置等待
            if int(self.collector.controller["sleepBeforeRun"]) > 0:
                sleep(int(self.collector.controller["sleepBeforeRun"]))
                self.test.debugLog("请求前等待%sS" % int(self.collector.controller["sleepBeforeRun"]))
            start_time = datetime.datetime.now()
            # 判断是否使用session
            if self.collector.controller["useSession"].lower() == 'true' and self.collector.controller[
                "saveSession"].lower() == "true":
                res = self.session.request(self.collector.method, url, **self.collector.others)
            elif self.collector.controller["useSession"].lower() == "true":
                session = deepcopy(self.session)
                res = session.request(self.collector.method, url, **self.collector.others)
            elif self.collector.controller["saveSession"].lower() == "true":
                session = Session()
                res = session.request(self.collector.method, url, **self.collector.others)
            else:
                res = request(self.collector.method, url, **self.collector.others)
            if self.collector.others.get('data'):
                DebugLogger("开始请求，请求参数为{}，请求路径为{}".format(
                    json.dumps(self.collector.others['data'], ensure_ascii=True), url))
            end_time = datetime.datetime.now()
            # 记录结束时间、保存响应结果
            self.test.recordTransDuring(int((end_time - start_time).microseconds / 1000))
            self.save_response(res)
            # 输出日志
            request_log += '<br>【请求完整链接】:{}<br>'.format(url)
            # request_log += '<br>【请求参数】:{}<>'.format(self.collector.controller)
            self.test.debugLog(request_log[:])
            response_log = '【响应信息】:<br>'
            response_log += '响应码: {}<br>'.format(self.status_code)
            response_log += '响应头: {}<br>'.format(dict2str(self.response_headers))
            if 'content-disposition' not in [key.lower() for key in self.response_headers.keys()]:
                response_text = '<b>响应体: {}</b>'.format(log_msg(self.response_content))
            else:
                response_text = '<b>响应体: 文件内容暂不展示, 长度{}</b>'.format(len(self.response_content_bytes))
            # 响应体长度不能超过50000
            response_log += response_text
            self.test.debugLog(response_log)
            # 断言
            self.check()
            # 关联参数
            self.extract_depend_params()
        finally:
            self.test.debugLog('[{}][{}]接口执行结束'.format(self.collector.apiId, self.collector.apiName))
            if int(self.collector.controller["sleepAfterRun"]) > 0:
                sleep(int(self.collector.controller["sleepAfterRun"]))
                self.test.debugLog("请求后等待%sS" % int(self.collector.controller["sleepAfterRun"]))

    def looper_controller(self, case, api_list, index):
        """循环控制器"""
        if "type" in self.collector.looper and self.collector.looper["type"] == "WHILE":
            # while循环 且兼容之前只有for循环
            loop_start_time = datetime.datetime.now()
            while self.collector.looper["timeout"] == 0 or (datetime.datetime.now() - loop_start_time).seconds * 1000 \
                    < self.collector.looper["timeout"]:     # timeout为0时可能会死循环 慎重选择
                # 渲染循环控制控制器 每次循环都需要渲染
                _looper = case._render_looper(self.collector.looper)
                result, _ = LMAssert(_looper['assertion'], _looper['target'], _looper['expect']).compare()
                if not result:
                    break
                _api_list = api_list[index - 1: (index + _looper["num"] - 1)]
                case._loop_execute(_api_list, api_list[index]["apiId"])
        else:
            # 渲染循环控制控制器 for只需渲染一次
            _looper = case._render_looper(self.collector.looper)
            for i in range(_looper["times"]):  # 本次循环次数
                self.context[_looper["indexName"]] = i + 1  # 给循环索引赋值第几次循环 母循环和子循环的索引名不应一样
                _api_list = api_list[index - 1: (index + _looper["num"] - 1)]
                case._loop_execute(_api_list, api_list[index]["apiId"])

    def condition_controller(self, case):
        """条件控制器"""
        _conditions = case._render_conditions(self.collector.conditions)
        for condition in _conditions:
            try:
                result, msg = LMAssert(condition['assertion'], condition['target'], condition['expect']).compare()
                if not result:
                    return msg
            except Exception as e:
                return str(e)
        else:
            return True

    def exec_script(self, code):
        """执行前后置脚本"""

        def sys_put(name, val):
            self.context[name] = val

        def sys_get(name):
            if name in self.params:  # 优先从公参中取值
                return self.params[name]
            return self.context[name]

        names = locals()
        names["res_code"] = self.status_code
        names["res_header"] = self.response_headers
        names["res_data"] = self.response_content
        names["res_cookies"] = self.response_cookies
        names["res_bytes"] = self.response_content_bytes
        names["send_body"] = self.collector.others
        # 将通用函数导入进来
        from tools.funclib.provider.lm_provider import CommonFunction
        exec(code)

    def save_response(self, res):
        """保存响应结果"""
        self.status_code = res.status_code
        self.response_headers = dict(res.headers)
        self.response_content_bytes = res.content
        s = ''
        for key, value in res.cookies.items():
            s += '{}={};'.format(key, value)
        self.response_cookies = s[:-1]
        try:
            self.response_content = res.json()
        except json.decoder.JSONDecodeError:
            self.response_content = res.text

    def extract_depend_params(self):
        """关联取值"""
        if self.collector.relations is not None:
            for items in self.collector.relations:
                if items['expression'].strip() == '$':
                    value = self.response_content_bytes
                elif items['expression'].strip().lower() in ['cookie', 'cookies']:
                    value = self.response_cookies
                else:
                    if items['from'] == 'resHeader':
                        data = self.response_headers
                    elif items['from'] == 'resBody':
                        data = self.response_content
                    elif items['from'] == 'reqHeader':
                        data = self.collector.others['headers']
                    elif items['from'] == 'reqQuery':
                        data = self.collector.others['params']
                    elif items['from'] == 'reqBody':
                        if self.collector.body_type == "json":
                            data = self.collector.others['json']
                        else:
                            data = self.collector.others['data']
                    else:
                        raise ExtractValueError('无法从{}位置提取依赖参数'.format(items['from']))
                    value = extract(items['method'], data, items['expression'])
                key = items['name']
                # 先将所有的关联取值都置为string
                self.context[key] = str(value)
                # self.context[key] = value

    def check(self):
        """断言"""
        check_messages = list()
        if self.collector.assertions is not None:
            results = list()
            for items in self.collector.assertions:
                try:
                    if items['from'] == 'resCode':
                        actual = self.status_code
                    elif items['from'] == 'resHeader':
                        actual = extract(items['method'], self.response_headers, items['expression'])
                    elif items['from'] == 'resBody':
                        actual = extract(items['method'], self.response_content, items['expression'])
                    else:
                        raise ExtractValueError('无法在{}位置进行断言'.format(items['from']))
                    result, msg = LMAssert(items['assertion'], actual, items['expect']).compare()
                except ExtractValueError as e:
                    result = False
                    msg = '接口响应失败或{}'.format(str(e))
                results.append(result)
                check_messages.append(msg)
                if not result:
                    break
            final_result = all(results)
        else:
            final_result, msg = LMAssert('相等', self.status_code, 200).compare()
            check_messages.append(msg)
        self.assert_result = {
            'apiId': self.collector.apiId,
            'apiName': self.collector.apiName,
            'result': final_result,
            'checkMessages': check_messages
        }

    def pop_content_type(self):
        pop_key = None
        for key, value in self.collector.others['headers'].items():
            if key.lower() == 'content-type':
                pop_key = key
                break
        if pop_key is not None:
            self.collector.others['headers'].pop(pop_key)


def dict2str(data):
    if isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False)
    elif not isinstance(data, str):
        return str(data)
    else:
        return data


def log_msg(value):
    temp_value = dict2str(value)
    temp_value_len = len(temp_value)
    if temp_value_len <= 15000:
        return temp_value
    else:
        return temp_value[:15000] + '...' + '数据长度{}超过15000, 暂不展示'.format(temp_value_len)


class RemoveParamError(Exception):
    """参数移除错误"""


class AssertRelationError(Exception):
    """断言关系错误"""


if __name__ == '__main__':
    from tools.funclib.provider.OSSFastUploadUtil import oss_util

    d = {
        "AccessKeyId": "STS.NSvS7b8uqJs8aZFP7fUsAAf2P",
        "AccessKeySecret": "43c2vWaBfLBUK5NDm6uXzpAQ9NLatJiiEiziRszAqr8t",
        "SecurityToken": "CAIS0QJ1q6Ft5B2yfSjIr5DDGI3W1apQ/bHTY3z3tDczWfxtrqOZsjz2IHhJe3VuAuoZv/01nm1T7PkelrNuUJJfZECeNpMtv89gqF3/OtOc6pDtvOJe1MUHnJ9Tz0apsvXJasDVEfkiE5XEMiI9/00e6L/+cirYAT7BGJaViJlhQ80KVw2jF1RvD8tXIQ0Q3q1/MmDKZ86wLjnggGfbECgNvRFn20xy9YO1wMCX9mDm7jvAx/QSup76L7W9csBoJ+0fadqu2/FsfaezjEwK4hNRpqBtl/4Gq3WVt9WZH0RMpg6aNPDd/dAqIxJ4erUnXLJBtL/BrtBC4LeLytWsjFRvRbgJAnuDHtH+npCaRbP2bowDGOylayiX4LemLYLotg4oW3UfOT5RdsApQn0KUkRxFW2EcfX4qQmQOFr4EffZysMtzYEw0k3s+tOGN/4CnUQJBZpyGoABFtTEFRWD7cF7Ba3SKxi3vYIG3viIU3L8DQgECWcdqYwfX+BVBQPhWrDGq5t/s82tR4B4q/TrL3ggiha/AgUlNh7YF0AhuEHH8ZXlpqOw6maguJw+951W1dwoRpUNkJDf20Gg/Fekrqi80748zWmtZuciDfBnvD/1Cq6HqM74QCw=",
        "ExpireTime": "2022-08-22T10:10:09Z"
    }
    print(
        oss_util(d['AccessKeyId'], d['AccessKeySecret'], d['SecurityToken']).upload_Url_selection('tmp/USER230593/', '',
                                                                                                  '/Users/liujin/Desktop/01682a5eef271ba801215aa0a8445d.jpg@1280w_1l_0o_100sh-opq2510515.jpg')
        )
    # import datetime
    # import hashlib
    # key = 'CSDtMH20ItRxAfEMauZuyLuA35Dd72V8'
    # time = int(datetime.datetime.now().timestamp())*1000
    # time_stamp = hex(int(time/1000))[2:]
    # # time_stamp = int('632c362a',16)
    # # print(time_stamp)
    # # print(1663835730 - 3600*8)
    # # print(time_stamp)
    # file = 'rest/v4c/fa/a2143115342/t{utctime}'.format(utctime=time)
    # hl = hashlib.md5()
    # str = key + '/' + file + time_stamp
    # print(str)
    # hl.update(str.encode(encoding='utf-8'))
    #
    # m = hl.hexdigest()
    # # # str = m.update(key+'/'+file+time_stamp)
    # print(m)
    # print('https://v4c.guituu.com/{sign}/{time_stamp}/{file}'.format(sign=m, time_stamp=time_stamp,file=file))
