#!/usr/bin/env python
# -*- coding:utf-8 -*-  
# ====#====#====#====
# Author:CXY
# CreateDate: 2022/8/17 18:04
# Filename:OSSFastUploadUtil.py
# Function:
# ====#====#====#====
import json
import os
import uuid
import base64
import oss2

from lm.lm_config import AlltuuConfig
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

config = AlltuuConfig()


class oss_util:
    def __init__(self, OssKeyId, OssKeySecret, OssToken, EndPoint=config.endpoint, Bucket=config.bucket):
        if OssToken is not None:
            auth = oss2.StsAuth(OssKeyId, OssKeySecret, OssToken)
        else:
            auth = oss2.Auth(OssKeyId, OssKeySecret)
        self.bucket = oss2.Bucket(auth, EndPoint, Bucket)
        self.OSSAccessKeyId = OssKeyId
        self.signature = OssKeySecret

    def upload_Url_selection(self, OssDir, file_seat, file, photoId=None):
        """
        sts 上传
        @param photoId:
        @param OssDir:  oss目录
        @param file_seat: 文件位置
        @param file: 上传文件
        @return: result,upload_id,remoteName 上传状态;视频上传ID;oss文件路径
        """
        total_size = os.path.getsize(file)
        KB_size = int(total_size / 1000)
        if file_seat == 'App_Image':
            remoteName, photoId, Suffix = self._App_remoteName(OssDir, file, photoId)
        else:
            photoId = uuid.uuid4().hex
            remoteName, photoId, Suffix = self._remoteName(OssDir, file_seat, file, photoId)
        try:
            url = self.bucket.sign_url('PUT', remoteName, 60, slash_safe=True)
            if self.bucket.put_object_with_url_from_file(url, file).status == 200:
                return KB_size, photoId, remoteName, Suffix
        except Exception as e:
            print(e)
            return None, None, None, None

    def upload_type_selection(self, OssDir, file_seat, file, photoId=None):
        """
        本地上传一般权限
        @param photoId:
        @param OssDir:  oss目录
        @param file_seat: 文件位置
        @param file: 上传文件
        @return: result,upload_id,remoteName 上传状态;视频上传ID;oss文件路径
        """
        total_size = os.path.getsize(file)
        KB_size = int(total_size / 1000)
        if file_seat == 'App_Image':
            remoteName, photoId, Suffix = self._App_remoteName(OssDir, file, photoId)
        else:
            photoId = uuid.uuid4().hex
            remoteName, photoId, Suffix = self._remoteName(OssDir, file_seat, file, photoId)
        try:
            if total_size < 1000000000000:
                if self._up_smallfile(remoteName, file).status == 200:
                    return KB_size, photoId, remoteName, Suffix
                else:
                    return None, None, None, None
            elif self._multipart_upload(remoteName, file):
                return KB_size, photoId, remoteName, Suffix
        except Exception as e:
            print(e)
            return None, None, None, None

    def upload_url(self, OssDir, file_seat, file, policy, signature, expire=60, photoId=None):
        total_size = os.path.getsize(file)
        KB_size = int(total_size / 1000)
        if file_seat == 'App_Image':
            remoteName, photoId, Suffix = self._App_remoteName(OssDir, file, photoId)
        else:
            photoId = uuid.uuid4().hex
            remoteName, photoId, Suffix = self._remoteName(OssDir, file_seat, file, photoId)
        params = {
            'signature': signature
        }
        # url = self.bucket.sign_url('PUT', remoteName, 60, slash_safe=True)

        url = 'http://alltuu-crm-guituu.oss-cn-hangzhou.aliyuncs.com/MALLCOUPON/couponId147/1.els?OSSAccessKeyId={}&Expires={}&Signature={}'.format(
            self.OSSAccessKeyId, expire, signature)
        print(url)
        if self.bucket.put_object_with_url_from_file(url, file).status == '200':
            return KB_size, photoId, remoteName, Suffix

    def upload_callback(self, OssDir, file_seat, file, callback, photoId=None):
        """
        一般权限增加回调地址,基本上不用，用的话需要向后端要到oss的appid和appsecret然后用Auth(appid, appsecret)来进行请求
        """
        total_size = os.path.getsize(file)
        KB_size = int(total_size / 1000)
        if file_seat == 'App_Image':
            remoteName, photoId, Suffix = self._App_remoteName(OssDir, file, photoId)
        else:
            photoId = uuid.uuid4().hex
            remoteName, photoId, Suffix = self._remoteName(OssDir, file_seat, file, photoId)
        # 设置上传回调参数。
        callback_obj = base64_to_dict(callback)
        callback_params = {'callbackUrl': callback_obj['callbackUrl'],
                           'callbackHost': callback_obj['callbackHost'],
                           'callbackBody': callback_obj['callbackBody'],
                           'callbackBodyType': callback_obj['callbackBodyType']}
        # 将callback_params转成base64格式
        encoded_callback = self.encode_callback(callback_params)
        # 将文件转成bytes和base64
        image_bytes, _ = file_to_base64_btyes(file)

        params = {'x-oss-callback': encoded_callback}
        # 填写Object完整路径和字符串。Object完整路径中不能包含Bucket名称。
        result = self.bucket.put_object(remoteName, image_bytes, params)
        # print(result.resp.response.content)
        return KB_size, photoId, remoteName, Suffix

    # 小文件上传
    def _up_smallfile(self, remoteName, file):
        return self.bucket.put_object_from_file(remoteName, file)

    # 分片上传
    def _multipart_upload(self, remoteName, file):
        total_size = os.path.getsize(file)
        # determine_part_size方法用于确定分片大小。
        part_size = determine_part_size(total_size, preferred_size=100 * 1024)
        # 初始化分片。秘钥
        # 如需在初始化分片时设置文件存储类型，请在init_multipart_upload中设置相关headers，参考如下。
        # headers = dict()
        # headers["x-oss-storage-class"] = "Standard"
        # upload_id = self.bucket.init_multipart_upload(remoteName, headers=headers).upload_id
        upload_id = self.bucket.init_multipart_upload(remoteName).upload_id
        parts = []
        # 逐个上传分片。
        with open(file, 'rb') as fileobj:
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)
                # 调用SizedFileAdapter(fileobj, size)方法会生成一个新的文件对象，重新计算起始追加位置。
                result = self.bucket.upload_part(remoteName, upload_id, part_number,
                                                 SizedFileAdapter(fileobj, num_to_upload))
                parts.append(PartInfo(part_number, result.etag))

                offset += num_to_upload
                part_number += 1
        # 完成分片上传。
        # 如需在完成分片上传时设置文件访问权限ACL，请在complete_multipart_upload函数中设置相关headers，参考如下。
        # headers = dict()
        # headers["x-oss-object-acl"] = oss2.OBJECT_ACL_PRIVATE
        # bucket.complete_multipart_upload(key, upload_id, parts, headers=headers)
        self.bucket.complete_multipart_upload(remoteName, upload_id, parts)
        # 验证分片上传。
        with open(file, 'rb') as fileobj:
            assert self.bucket.get_object(remoteName).read() == fileobj.read()
            return True

    # 拼接oss上传路径
    @staticmethod
    def _remoteName(OssDir, file_seat, file, photoId):
        (filepath, empFileName) = os.path.split(file)
        (filename, Suffix) = os.path.splitext(empFileName)
        Suffix = Suffix.split('.')[1]
        tmp = '.'
        # 判断是否上传本地的
        if file_seat == 'localVideo':
            Suffix = Suffix.lower()
            tmp = '-video-preview.'
        elif file_seat == 'localThirdImage':
            Suffix = Suffix.lower()
            tmp = '-video-cover-preview.'
        elif file_seat == 'watermark':
            Suffix = 'png'

        if Suffix == "JPG":
            Suffix = Suffix.lower()
        elif Suffix == 'mp4':
            Suffix = Suffix.upper()

        return os.path.join(OssDir, file_seat, photoId + tmp + Suffix), photoId, Suffix

        # 取消分片上传事件、

    # 拼接 App上传oss路径
    @staticmethod
    def _App_remoteName(OssDir, file, photoId):
        (filepath, empFileName) = os.path.split(file)
        (filename, Suffix) = os.path.splitext(empFileName)
        Suffix = Suffix.split('.')[1]
        if Suffix == "JPG":
            Suffix = Suffix.lower()
        elif Suffix == 'mp4':
            Suffix = Suffix.upper()
        return OssDir + photoId + '.' + Suffix, photoId, Suffix

    def recall_multipart_upload(self, remoteName, upload_id):
        self.bucket.abort_multipart_upload(remoteName, upload_id)

    # 列举已上传的分片信息
    def multipart_upload_info(self, remoteName, upload_id):
        for part_info in oss2.PartIterator(self.bucket, remoteName, upload_id):
            print('part_number:', part_info.part_number)
            print('etag:', part_info.etag)
            print('size:', part_info.size)

    # 定义回调参数Base64编码函数。
    @staticmethod
    def encode_callback(abc):
        cb_str = json.dumps(abc).strip()
        return oss2.compat.to_string(base64.b64encode(oss2.compat.to_bytes(cb_str)))

    # 文件大小转换
    @staticmethod
    def size_format(size):
        if size < 1000:
            return '%i' % size + 'size'
        # elif 1000 <= size < 1000000:
        #     return '%.1f' % float(size / 1000) + 'KB'
        elif 1000 <= size:
            return '%.1f' % int(size / 1000) + 'KB'
        # elif 1000000 <= size < 1000000000:
        #     return '%.1f' % float(size / 1000000) + 'MB'
        # elif 1000000000 <= size < 1000000000000:
        #     return '%.1f' % float(size / 1000000000) + 'GB'
        # elif 1000000000000 <= size:
        #     return '%.1f' % float(size / 1000000000000) + 'TB'


# 解析host
def resolve_host(host: str):
    Bucket, end_point = host.split('.', 1)
    http, Bucket = Bucket.split('//', 1)
    end_point = http + '//' + end_point
    return end_point, Bucket


def base64_to_dict(data):
    a = base64.b64decode(data).decode('UTF-8')
    f = json.loads(a)
    return f


def file_to_base64_btyes(file):
    with open(file, 'rb') as f:
        image_bytes = f.read()
        image_base64 = str(base64.b64decode(image_bytes))
    return image_bytes, image_base64


class CommonFunction:
    # 上传文件
    @staticmethod
    def oss_upload_file(res_data, send_body, oss_type, oss_dir, file_seat):
        oss = None

        for filename, value in send_body['files'].items():
            with open(filename, 'wb') as f:
                f.write(value)
            if oss_type == '4':
                oss = oss_util(config.KeyId, config.KeySecret, None)
                KB_size, uuid_name, fileName, Suffix = oss.upload_Url_selection(res_data['key'], file_seat, filename)
            elif oss_type == '9':
                oss = oss_util(res_data['AccessKeyId'], res_data['AccessKeySecret'], res_data['SecurityToken'])
                KB_size, uuid_name, fileName, Suffix = oss.upload_Url_selection(oss_dir, file_seat, filename)
            else:
                oss = oss_util(res_data['AccessKeyId'], res_data['AccessKeySecret'], res_data['SecurityToken'])
                KB_size, uuid_name, fileName, Suffix = oss.upload_Url_selection(oss_dir, file_seat, filename)
            os.remove(filename)

            if KB_size is not None:
                return KB_size, uuid_name, fileName, Suffix
            else:
                raise Exception('文件上传失败')


#

if __name__ == '__main__':
    send_body = {'files': {
        '/Users/liujin/pyProject/Liuma-engine/fileName.jpg': '/Users/liujin/pyProject/Liuma-engine/fileName.jpg'}}
    d = {'accessid': 'LTAI5tKT2R6mXMqMp9NMdZiU', 'key': 'tmp/USER10007133/',
         'policy': 'eyJleHBpcmF0aW9uIjoiMjAyMy0wMy0yMFQxMDoxNjo0NS4zMjdaIiwiY29uZGl0aW9ucyI6W1siY29udGVudC1sZW5ndGgtcmFuZ2UiLDAsNTM2ODcwOTEyMF0sWyJzdGFydHMtd2l0aCIsIiRrZXkiLCJ0bXAvVVNFUjEwMDA3MTMzLyJdXX0=',
         'signature': 'XIl3aJSratJvru/CCzb1V83MOhk=', 'dir': 'tmp/USER10007133/', 'host': 'https://ssa.guituu.com',
         'expire': '1679307405', 'bucket': 'alltuu-storage-guituu',
         'callback': 'eyJjYWxsYmFja1VybCI6ImN0Lmd1aXR1dS5jb20vcmVzdC92NC9jbG91ZC9waG90by9jb21tb24vbm90aWZ5IiwiY2FsbGJhY2tIb3N0IjoiY3QuZ3VpdHV1LmNvbSIsImNhbGxiYWNrQm9keSI6ImJ1Y2tldD0ke2J1Y2tldH0mZmlsZW5hbWU9JHtvYmplY3R9JnNpemU9JHtzaXplfSZtaW1lVHlwZT0ke21pbWVUeXBlfSZoZWlnaHQ9JHtpbWFnZUluZm8uaGVpZ2h0fSZ3aWR0aD0ke2ltYWdlSW5mby53aWR0aH0mZm9ybWF0PSR7aW1hZ2VJbmZvLmZvcm1hdH0mdXNlcklkPTEwMDA3MTMzJmFsYnVtSWROPTUxMzM1MTI0NTciLCJjYWxsYmFja0JvZHlUeXBlIjoiYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkIn0='}
    CommonFunction.oss_upload_file(d, send_body, '4', 'tmp/USER10007133/', 'poster')
