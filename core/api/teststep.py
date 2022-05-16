import datetime
from time import sleep
from requests import request, Session
from copy import deepcopy
from jsonpath_ng.parser import JsonPathParser
import json
import jsonpath

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

    def __init__(self, test, session, collector, context):
        self.session = session
        self.collector = collector
        self.context = context
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
            request_log += '【请求URL】{} {}<br>'.format(self.collector.method,
                                                     url_join(self.collector.url, self.collector.path))
            # self.collector.others.update({'params': self.collector.others['query']})
            # del self.collector.others['query']

            request_log += '<br>【其他的一些参数】：<br>'

            # print(self.collector.url, self.collector.path, self.collector.protocol)
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
            if bool(self.collector.controller["useSession"]) and bool(self.collector.controller["saveSession"]):
                res = self.session.request(self.collector.method, url, **self.collector.others)
            elif bool(self.collector.controller["useSession"]):
                session = deepcopy(self.session)
                res = session.request(self.collector.method, url, **self.collector.others)
            elif bool(self.collector.controller["saveSession"]):
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
                a = log_msg(res.text, default=1)
                print(a)
                response_text = '响应体: {}'.format(a.replace("\n", "<br>"))
            else:
                response_text = '响应体: 文件内容暂不展示, 长度{}'.format(len(res.text))
            response_log += response_text
            self.test.debugLog(response_log)
            self.check()
            if self.assert_result['result']:
                self.extract_depend_params()
        finally:
            self.test.debugLog('[{}][{}]接口执行结束'.format(self.collector.apiId, self.collector.apiName))
            if int(self.collector.controller["sleepAfterRun"]) > 0:
                sleep(int(self.collector.controller["sleepAfterRun"]))
                self.test.debugLog("请求后等待%sS" % int(self.collector.controller["sleepAfterRun"]))

    def save_response(self, res):
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
        tmp_data = deepcopy(data)
        if len(tmp_data) > 0:
            parser = JsonPathParser()
            for i, j in zip(jsonpath.jsonpath(tmp_data, '$..'), jsonpath.jsonpath(tmp_data, '$..', result_type="PATH")):
                expr = parser.parse(j)
                if isinstance(i, bytes):
                    expr.update(tmp_data, '字节数据暂不展示, 长度为{}'.format(len(i)))
        return json.dumps(tmp_data, ensure_ascii=False, indent=4)
    elif not isinstance(data, str):
        return str(data)
    else:
        return data


def log_msg(value, default=0):
    try:
        if default == 1:
            value = json.loads(value)
    except:
        pass
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


if __name__ == '__main__':
    a = '{ "code": 0, "message": "0", "ttl": 1, "data": { "items": [ { "doc_id": 194355039, "poster_uid": 512313464, "title": "", "description": "大家好，本周是GAMES重磅推出《可视化研究生成长经验分享》系列论坛第四期。\n\n本期的两位老师将为我们分享关于 “科学可视化” 以及 “多维数据可视化”的科研经验和心得体会。\n\n欢迎关注今晚八点的直播[吃瓜][吃瓜]", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/d67fd7f376c2de59de6f5f9fb89314862888a23b.jpg", "img_width": 1684, "img_height": 1052, "img_size": 86.349609375, "img_tags": null } ], "count": 1, "ctime": 1652355320, "view": 14108, "like": 38, "dyn_id": "659350150782648329" }, { "doc_id": 194088730, "poster_uid": 512313464, "title": "", "description": "又到周一了，今晚八点有 GAMES104 第八课哦~\r\n同学们不要忘记了[打call]", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/7c3f19de039ec8501396f60cf63d9ff8f1a9da1b.jpg", "img_width": 1001, "img_height": 626, "img_size": 279.3330078125, "img_tags": null } ], "count": 1, "ctime": 1652088852, "view": 15655, "like": 136, "dyn_id": "658205679460286470" }, { "doc_id": 193755162, "poster_uid": 512313464, "title": "", "description": "大家好，本周是GAMES重磅推出的《可视化研究生成长经验分享》系列论坛第三期。\n\n本期的两位学姐将给我们分享 “跨专业读博的苦与乐” 以及 “userStudy的书写经验”\n\n今晚八点，锁定直播间[打call][打call]", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/d67fd7f376c2de59de6f5f9fb89314862888a23b.jpg", "img_width": 1684, "img_height": 1052, "img_size": 86.349609375, "img_tags": null } ], "count": 1, "ctime": 1651742379, "view": 14116, "like": 58, "dyn_id": "656717589255290884" }, { "doc_id": 192875211, "poster_uid": 512313464, "title": "", "description": "又到周一了，今晚八点有 GAMES104 第七课哦~\r\n同学们不要忘记了[打call]", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/7c3f19de039ec8501396f60cf63d9ff8f1a9da1b.jpg", "img_width": 1001, "img_height": 626, "img_size": 279.3330078125, "img_tags": null } ], "count": 1, "ctime": 1650881289, "view": 16656, "like": 147, "dyn_id": "653019235864281108" }, { "doc_id": 192262800, "poster_uid": 512313464, "title": "", "description": "又到周一了，今晚八点有 GAMES104 第六课哦~\n同学们不要忘记了[打call]", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/bffa5814ec3a627be67b5893e27b9a78bba9588b.jpg", "img_width": 1001, "img_height": 626, "img_size": 659.41015625, "img_tags": null } ], "count": 1, "ctime": 1650279853, "view": 16413, "like": 181, "dyn_id": "650436088129650690" }, { "doc_id": 191033018, "poster_uid": 512313464, "title": "", "description": "今晚8点就是 GAMES104 第四课啦，假期不间断，小伙伴们别错过了~", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/bffa5814ec3a627be67b5893e27b9a78bba9588b.jpg", "img_width": 1001, "img_height": 626, "img_size": 659.41015625, "img_tags": null } ], "count": 1, "ctime": 1649063418, "view": 18960, "like": 173, "dyn_id": "645211539432800312" }, { "doc_id": 190191274, "poster_uid": 512313464, "title": "", "description": "感谢@爱学习的校园君 的支持！小伙伴们，今晚8点GAMES104第三节课准时开始~https://www.bilibili.com/blackboard/activity-Pxtwy1uq3I.html?spm_id_from=444.42.0.0 ", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/bffa5814ec3a627be67b5893e27b9a78bba9588b.jpg", "img_width": 1001, "img_height": 626, "img_size": 659.41015625, "img_tags": null } ], "count": 1, "ctime": 1648464249, "view": 17295, "like": 125, "dyn_id": "642638128159391783" }, { "doc_id": 183186012, "poster_uid": 512313464, "title": "", "description": "大家好，GAMES在春节过后将会邀请不鸣科技CEO，《战意》制作人王希进行GAMES 104《现代游戏引擎：从入门到实践》的授课。 \n\n想知道带给我们无数欢乐的游戏是怎样创造出来的吗？王希学长手把手，带你从0-1搭建一个属于自己的游戏引擎！本课程涵盖所有游戏引擎知识，欢迎大家关注3月开课的GAMES 104！ [脱单doge][脱单doge]", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/album/257045b94159dbf94c5f0d490900e3d28a613605.jpg", "img_width": 1080, "img_height": 834, "img_size": 81.76171875, "img_tags": null } ], "count": 1, "ctime": 1642174496, "view": 26758, "like": 411, "dyn_id": "615623844662760591" }, { "doc_id": 57470470, "poster_uid": 512313464, "title": "", "description": "我已成为哔哩哔哩第65155207位转正会员，挑战转正答题考试获得61分，获得\"学霸\"挂件，有效期8天。", "pictures": [ { "img_src": "https://i0.hdslb.com/bfs/member/b589cc0ebfe818b6c0a1f01a30f8f9020b949da7.png", "img_width": 750, "img_height": 750, "img_size": 300, "img_tags": null } ], "count": 1, "ctime": 1582342355, "view": 1440, "like": 5, "dyn_id": "358646755819935423" } ] } }'
    b = '{ "name":"Bill", "age":63, "city":"Seatle"}'
    print(log_msg(b, 1))
