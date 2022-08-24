from functools import reduce
from faker.providers import BaseProvider
import time
from lm.lm_api import LMApi
from pypinyin import lazy_pinyin
import base64
import datetime
import json
from dateutil.relativedelta import relativedelta


class LiuMaProvider(BaseProvider):

    @staticmethod
    def lm_custom_func(code, params):
        def func(self, *args):
            def sys_return(res):
                names["_exec_result"] = res
            names = locals()
            for index, value in enumerate(params):
                names[value] = args[index]
            exec(code)
            return names["_exec_result"]
        return func

    def loadfile(self, uuid):
        try:
            res = LMApi().download_test_file(uuid)
        except:
            raise Exception("拉取测试文件失败")
        else:
            return res.content

    def b64encode_str(self, s: str):
        return base64.b64encode(s.encode('utf-8')).decode()

    def b64encode_bytes(self, s: bytes):
        return base64.b64encode(s).decode()

    def b64encode_file(self, uuid):
        content = self.loadfile(uuid)
        return base64.b64encode(content).decode()

    def b64decode_toStr(self, s: str):
        return base64.b64decode(s).decode()

    def b64decode_toBytes(self, s: str):
        return base64.b64decode(s)

    def arithmetic(self, expression: str):
        try:
            return eval(expression)
        except Exception:
            raise Exception("四则运算表达式错误:%s" % expression)

    def current_time(self, s: str = '%Y-%m-%d'):
        if s.lower() == "none":
            return int(time.time() * 1000)
        return time.strftime(s)

    def year_shift(self, shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        shift_date = now_date + relativedelta(years=shift)
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def month_shift(self, shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        shift_date = now_date + relativedelta(months=shift)
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def week_shift(self, shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(weeks=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def date_shift(self, shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(days=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def hour_shift(self, shift, s: str = '%Y-%m-%d %H:%M:%S'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(hours=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def minute_shift(self, shift, s: str = '%Y-%m-%d %H:%M:%S'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(minutes=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def second_shift(self, shift, s: str = '%Y-%m-%d %H:%M:%S'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(seconds=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    def lenof(self, array):
        return len(array)

    def indexof(self, array, index):
        return array[index]

    def keyof(self, map, key):
        return map[key]

    def pinyin(self, cname: str):
        return reduce(lambda x, y: x + y, lazy_pinyin(cname))

    def substing(self, s, start: int = 0, end: int = -1):
        return s[start:end]

    def extract(self, data):
        return data

    def replace(self, s, old, new):
        return s.replace(old, new)

    def map_dumps(self, tar):
        return json.dumps(tar)

    def array_dumps(self, tar):
        return json.dumps(tar)


class CommonFunction:
    # 上传文件
    @staticmethod
    def oss_upload_file(res_data, send_body, oss_type, oss_dir, file_seat):
        from tools.funclib.provider.OSSFastUploadUtil import oss_util
        from lm.lm_config import AlltuuConfig
        import os
        config = AlltuuConfig()
        oss = None

        for filename, value in send_body['files'].items():
            with open(filename, 'wb') as f:
                f.write(value)
            if oss_type == '4':
                oss = oss_util(config.KeyId, config.KeySecret, None)
                KB_size, uuid_name, fileName, Suffix = oss.upload_callback(res_data['key'], file_seat, filename,
                                                                           res_data['callback'])
            else:
                oss = oss_util(res_data['AccessKeyId'], res_data['AccessKeySecret'], res_data['SecurityToken'])
                KB_size, uuid_name, fileName, Suffix = oss.upload_Url_selection(oss_dir, file_seat, filename)

            os.remove(filename)

            if KB_size is not None:
                return KB_size, uuid_name, fileName, Suffix
            else:
                raise Exception('文件上传失败')
