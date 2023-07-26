import os
from functools import reduce
from faker.providers import BaseProvider
import time
from lm.lm_api import LMApi
from pypinyin import lazy_pinyin
import base64
import datetime
import json
from dateutil.relativedelta import relativedelta
from lm.lm_config import FILE_PATH


class LiuMaProvider(BaseProvider):

    @staticmethod
    def lm_custom_func(code, params):
        """返回自定义函数方法"""

        def func(self, *args):
            def sys_return(res):
                """定义了返回数值的函数"""
                names["_exec_result"] = res

            names = locals()
            for index, value in enumerate(params):
                names[value] = args[index]
            exec(code)
            return names["_exec_result"]

        return func

    @staticmethod
    def loadfile(uuid):
        try:
            res = LMApi().download_test_file(uuid)
        except:
            raise Exception("拉取测试文件失败")
        else:
            return res.content

    @staticmethod
    def savefile(uuid):
        try:
            res = LMApi().download_test_file(uuid)
        except:
            raise Exception("拉取测试文件失败")
        else:
            file_name = res.headers.get("Content-Disposition").split("=")[1][1:-1]
            dir_path = os.path.join(FILE_PATH, uuid)
            file_path = os.path.join(dir_path, file_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                with open(file_path, 'wb+') as f:
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                f.close()
            return file_path

    @staticmethod
    def b64encode_str(s: str):
        return base64.b64encode(s.encode('utf-8')).decode()

    @staticmethod
    def b64encode_bytes(s: bytes):
        return base64.b64encode(s).decode()

    def b64encode_file(self, uuid):
        content = self.loadfile(uuid)
        return base64.b64encode(content).decode()

    @staticmethod
    def b64decode_toStr(s: str):
        return base64.b64decode(s).decode()

    @staticmethod
    def b64decode_toBytes(s: str):
        return base64.b64decode(s)

    @staticmethod
    def arithmetic(expression: str):
        try:
            return eval(expression)
        except Exception:
            raise Exception("四则运算表达式错误:%s" % expression)

    @staticmethod
    def current_time(s: str = '%Y-%m-%d'):
        if s.lower() == "none":
            return int(time.time() * 1000)
        return time.strftime(s)

    @staticmethod
    def year_shift(shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        shift_date = now_date + relativedelta(years=shift)
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def month_shift(shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        shift_date = now_date + relativedelta(months=shift)
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def week_shift(shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(weeks=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def date_shift(shift, s: str = '%Y-%m-%d'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(days=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def hour_shift(shift, s: str = '%Y-%m-%d %H:%M:%S'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(hours=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def minute_shift(shift, s: str = '%Y-%m-%d %H:%M:%S'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(minutes=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def second_shift(shift, s: str = '%Y-%m-%d %H:%M:%S'):
        now_date = datetime.datetime.now()
        delta = datetime.timedelta(seconds=shift)
        shift_date = now_date + delta
        if s.lower() == "none":
            return int(shift_date.timestamp() * 1000)
        return shift_date.strftime(s)

    @staticmethod
    def lenof(array):
        return len(array)

    @staticmethod
    def indexof(array, index):
        return array[index]

    @staticmethod
    def keyof(map, key):
        return map[key]

    @staticmethod
    def pinyin(cname: str):
        return reduce(lambda x, y: x + y, lazy_pinyin(cname))

    @staticmethod
    def substing(s, start: int=0, end: int=-1):
        return s[start:end]

    @staticmethod
    def extract(data):
        return data

    @staticmethod
    def replace(s, old, new):
        return s.replace(old, new)

    @staticmethod
    def map_dumps(tar):
        return json.dumps(tar)

    @staticmethod
    def array_dumps(tar):
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
