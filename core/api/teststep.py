import datetime
from time import sleep
from requests import request, Session
from copy import deepcopy
import json

from core.assertion import LMAssert
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
        self.params = params
        self.test = test
        self.status_code = None
        self.response_headers = None
        self.response_content = None
        self.response_content_bytes = None
        self.response_cookies = None
        self.assert_result = None

    def execute(self):
        try:
            self.test.debugLog('[{}][{}]接口执行开始'.format(self.collector.apiId, self.collector.apiName))
            request_log = '【请求信息】:<br>'
            request_log += '{} {}<br>'.format(self.collector.method, url_join(self.collector.url, self.collector.path))
            for key, value in self.collector.others.items():
                if value is not None:
                    c_key = REQUEST_CNAME_MAP[key] if key in REQUEST_CNAME_MAP else key
                    if key == 'files':
                        if isinstance(value, dict):
                            request_log += '{}: {}<br>'.format(c_key, [i[0] for i in value.values()])
                        if isinstance(value, list):
                            request_log += '{}: {}<br>'.format(c_key, [i[1][0] for i in value])
                    else:
                        request_log += '{}: {}<br>'.format(c_key, log_msg(value))
            self.test.debugLog(request_log[:-4])
            if self.collector.body_type == "form-urlencoded":
                self.collector.others['data'] = urlencode(self.collector.others['data'])
            if 'files' in self.collector.others and self.collector.others['files'] is not None:
                self.pop_content_type()
            url = url_join(self.collector.url, self.collector.path)
            if int(self.collector.controller["sleepBeforeRun"]) > 0:
                sleep(int(self.collector.controller["sleepBeforeRun"]))
                self.test.debugLog("请求前等待%sS" % int(self.collector.controller["sleepBeforeRun"]))
            start_time = datetime.datetime.now()
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
            end_time = datetime.datetime.now()
            self.test.recordTransDuring(int((end_time - start_time).microseconds / 1000))
            self.save_response(res)
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

    def judge_condition(self):
        conditions = json.loads(self.collector.controller["whetherExec"])
        for condition in conditions:
            try:
                result, msg = LMAssert(condition['assertion'], condition['target'], condition['expect']).compare()
                if not result:
                    return msg
            except Exception as e:
                return str(e)
        else:
            return True

    def loop_exec(self):
        loop = json.loads(self.collector.controller["loopExec"])
        print(loop)
        _loop_index_name = loop["indexName"]
        try:
            _loop_times = int(loop["times"])
        except:
            _loop_times = 1
        try:
            _loop_num = int(loop["num"])
        except:
            _loop_num = 1
        return _loop_index_name, _loop_times, _loop_num

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
        """关联参数"""
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
                self.context[key] = value

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
        return '数据长度{}超过15000, 暂不展示'.format(temp_value_len)


class RemoveParamError(Exception):
    """参数移除错误"""


class AssertRelationError(Exception):
    """断言关系错误"""
