import binascii
import os
import time
import uuid
from hashlib import md5
from urllib.parse import unquote

from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5

from lm.lm_config import AlltuuConfig

# from requests.packages.urllib3.exceptions import InsecureRequestWarning

# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

private_key = '-----BEGIN RSA PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCXQ0JiyBFg+/5ISNodNzSWA6hHR/lFPhd1HZSk//iiX0P0fx/y5SoOtxuessxQhauNAdcjMQaDsOf8j0wp+VbX18UDQMbhUEsAVOOoGxLt8nGjWOgG1RVGAkLEo4KoBNtpFqCZzYH5HCO7QO1amn3pEDqL52w5oUSIqdSnlRLpoDSC8lSa7lbDBUKuWMQHbRc/I3q4N7tY10BE0qfAUHS46qiBTI0jI2HSfH8qQUNOl4+x4+frUhnDVEhJ0XN3qkuL5yU6DII+AYa59nL2vLOwQfKTCgX4ZsNoC2idMizNF9Te+gaRldnn3qkqCixJM0n9RO1JKo+6kpii4MSi+85jAgMBAAECggEAIsS7BamnFPvXPxY/zGdcFv9QNtI8YcYb7jeWazbLF8d9/z0ZQuOZ/zfniVrfy8Jt5EOAB/7E2JBZQpxNjXhaldJq3oyNKk0icDkS+xj+COOpazqMWsWv1h++6SQMbEJxjH4+/BtYvMHTFL+fzyujtWadjnrrTXPcJO2ki8CgUELALtQmJaqIIqnLi0jmODsGQZHsdieQkth544dPKaBLS0aaH3lyyPu2dmlGLsrcFWm4ZJUuKD3I5F3VgsLijFyHDVVMTK8aSY16c702rFp29n0m/K51q0pw34wcTsXCPCrO1+s4KgULZeWxCO/NqYk1qTkdJnBQYsBRotOR3G8KQQKBgQDQ7uB+aGsotMfLmPT24ejkkcJ5/zX/uCVyqITGnM3REHZbNuDQpJZP1xai9ferG2UrsUrbFk6t/yF8xcGBcmAWsBpYrnuqWnTNBtVPHFNbTRdkhypTwn8kk4o7ekfcys06aZ/s5gQkLiuNarOfkQerAqlSSay4mCCbb19NGxvpJQKBgQC5VouQ91x4eEA29pbCHXlY8CEAldzGdof8LKqNyJEaSNjQykrMFm+2uKY5VMM5TMsaev89jBNO6GI19Qhgsw3JBBqsJ5UTSg/8+dSxfWZvE0qux6stoFqzu60o33KFRRg/3gA712TA0tUdZvRHfxbVdHFaBRvWieTLhllH8nJW5wKBgQDOy0CDnRJDLft6tp/vI9aBNQvJ+CIYQsk93THd6yGDRcn/qieGGwFzcK5FCTLjtq/COS6f/kpNyXH5rzpBx1T338GT+M8J45IrxBGoxZ5zhbAbnfT1BlMVfrqY+ATcshXDNPxHW7rJnLEavXuf+cofJvk0Kxu7cUcE0Y0AIk7TyQKBgGvJO03JrguZ066jZjXqMkJZFLhkb4s0MA2mZGIkvM6OgxmaLDnY6otXg8Rf2VGfqZby5TIEHs6LM2Kx6HdkaqX3LxPjyTz4m6fCG8JFbac3jv1qvdDBKz7P7PqSSOXcsyehkn063SuO8cYxs+tIrBzjpXB2/COe+mKq9Y10IK8NAoGBAKowF8Oda3w0fnOhjZDNiHbknGwYv2wcqJWiO/1WMEW/B2afWreYDIarf1kBRr+oy1uEncd09RhBeu2bf+GbB4GEOex4hC5q1d3VdYt5yKA9Ix0OfmgdEwUucjLP8OcTOWXHbBOiJ7Qf9DLTc1DzHc1h8xN44R9GVANt7LKgYXGY\n-----END RSA PRIVATE KEY-----'
MAXLINESIZE = 76  # Excluding the CRLF
MAXBINSIZE = (MAXLINESIZE // 4) * 3

#  requests  加密规则
PC_source = '100101'


def ama_path_join(args):
    # 有一处接口用到的顺序需要保持和获取到的一致，所以不能在这里调整顺序
    # return os.path.join(*[key + str(args[key]) for key in sorted(args.keys())])
    return os.path.join(*[key + value for key, value in args.items()])


class Signature:
    @staticmethod
    def open_sign_url(appKey, secretKey, args_map):
        """
        派瞬开放文档相关
        接口加密
        @param appKey: 应用id
        @param secretKey: 密钥
        @param args_map: 请求参数
        @return:拼接接口请求体, 加密参数
        """
        timestamp = str(int(time.time() * 1000))  # 请求发起时间戳        # timestamp ='1627525820470'  # 请求发起时间戳
        std_args_map = {"timestamp": timestamp, "appKey": appKey, "secretKey": secretKey}
        signature_generate = Signature().Encryption_args_map(args_map, std_args_map)
        signature_string = "%s-%s-%s" % (appKey, timestamp, signature_generate)
        return signature_string, signature_generate

    # sign_url_v4 返回V4签名
    def sign_url_v4(self, token, args_map, source=PC_source, limit=False, no_sign_date=None):
        """
        sign_url_v4 返回V4签名
        @param token: 用户token
        @param source: 版本
        @param no_sign_date: 是否加密
        @param args_map: 请求参数
        @param limit: 是否限流
        @return:拼接接口请求体, 加密参数
        """
        if source is None:
            source = PC_source
        if no_sign_date is not None:
            for del_item in no_sign_date:
                del args_map[del_item]
        # 如果参数中存在v，那就将接口的版本改为对应的v  -- 应为有一个接口中存在v影响到了
        if 'v' in args_map:
            api_v = args_map['v']
            del args_map['v']
        else:
            api_v = '0'
        timestamp = str(int(time.time() * 1000))  # 请求发起时间戳
        std_args_map = {"from": source, "timestamp": timestamp, "token": token, "version": api_v}
        # 把标准的四个参数组成的map和非标准参数args_map合并成一个map, 用来进行签名
        signature_generate = self.Encryption_args_map(args_map, std_args_map)
        signature_string = "%s-%s-%s-%s-%s" % (source, timestamp, token, api_v, signature_generate)
        if limit:
            Guid = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(uuid.uuid1()))).replace("-", "")
            signature_string += "-%s" % Guid
        return signature_string, signature_generate

    # 对签名字符串进行 rsa2签名
    @staticmethod
    def sign_rsa2(content):
        """对签名字符串进行 rsa2签名"""

        items = sorted(content.items())
        validate_string_array = [value for key, value in items]
        signer = PKCS1_v1_5.new(RSA.importKey(private_key))
        rand_hash = SHA256.new()

        string_to_be_signatures1 = ""
        string_to_be_signatures1 += "".join(validate_string_array)
        rand_hash.update(string_to_be_signatures1.encode('utf-8'))
        signature = signer.sign(rand_hash)
        # 将换行符
        sign = Signature().encodebytes(signature).decode("utf8").replace("\n", "")
        return sign

    # 将传入的字符串编码为包含多行base-64数据的字节对象。
    @staticmethod
    def encodebytes(s):
        """
         Encode a testing into a bytes object containing multiple lines
        of base-64 data.
        将传入的字符串编码为包含多行base-64数据的字节对象。

        """
        Signature()._input_type_check(s)
        pieces = []
        # 将字符串分割成小块，转化为base64形式
        for i in range(0, len(s), MAXBINSIZE):
            chunk = s[i: i + MAXBINSIZE]
            pieces.append(binascii.b2a_base64(chunk))
        # 返回b""的字符串
        return b"".join(pieces)

    # 判断是不是符合要求的数据类型
    @staticmethod
    def _input_type_check(s):
        """
        判断是不是符合要求的数据类型

        """
        try:
            # memoryview() 函数返回给定参数的内存查看对象
            m = memoryview(s)
        except TypeError as err:
            msg = "expected bytes-like object, not %s" % s.__class__.__name__
            raise TypeError(msg) from err
        # 判断传入数据的编码
        if m.format not in ('c', 'b', 'B'):
            msg = ("expected single byte elements, not %r from %s" %
                   (m.format, s.__class__.__name__))
            raise TypeError(msg)
        # 判断是不是一维的数据，不是的话报错
        if m.ndim != 1:
            msg = ("expected 1-D data, not %d-D data from %s" %
                   (m.ndim, s.__class__.__name__))
            raise TypeError(msg)

    @staticmethod
    def Encryption_args_map(args_map, std_args_map):
        validate_map = {}
        if args_map is None:
            validate_map = dict(std_args_map)
        elif isinstance(args_map, dict):
            validate_map = dict(args_map, **std_args_map)
        # 把所有参数按照参数名称进行字典序升序排序
        items = sorted(validate_map.items())
        validate_string_array = [value for key, value in items]
        string_to_be_signatures = "/"
        string_to_be_signatures += "/".join(validate_string_array)
        # 对签名字符串进行md5签名
        md5_generator = md5()
        md5_generator.update(string_to_be_signatures.encode('utf-8'))
        signature_generate = md5_generator.hexdigest()
        return signature_generate

    @staticmethod
    def concatenating_url(args_map):
        """拼接URL"""

        return ama_path_join(args_map)

    @staticmethod
    def decode_url(args_map):
        args_map = args_map.replace('+', "%20")
        str_list = []
        for i in unquote(args_map).split('&'):
            str_list.append(i.split('='))
        return dict(str_list)

    @staticmethod
    def sign_url_v4c(path, args_map):
        import hashlib
        # 直播相册加密
        file_path = os.path.join(path, ama_path_join(args_map))
        alltuu_config = AlltuuConfig()
        time_stamp = hex(args_map['t'] // 1000)[2:]
        hl = hashlib.md5()
        hl.update((alltuu_config.CDNKey + '/' + file_path + time_stamp).encode(encoding='utf-8'))
        return '/{sign}/{time_stamp}/{file}'.format(sign=hl.hexdigest(), time_stamp=time_stamp, file=file_path)


# def decode_url(args_map):
#     args_map = args_map.replace('+', "%20")
#     str_list = []
#     for i in unquote(args_map).split('&'):
#         str_list.append(i.split('='))
#     return dict(str_list)


if __name__ == '__main__':
    # strl = 'name=15191333333&pwd=25d55ad283aa400af464c76d713c07ad'
    # arg = {}
    # str_list = []
    # for i in strl.split('&'):
    #     str_list.append(i.split('='))
    # dict_map = dict(str_list)
    # print(dict_map)
    # print(Signature.sign_url_v4c('rest/v4c/fa', {"a": '123', 't': 123412312312}))
    print(Signature.concatenating_url({'2': 3, '1': 1}))
