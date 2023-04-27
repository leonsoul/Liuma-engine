# -*- coding: utf-8 -*-
# @ModuleName: Redis.py
# @Function: R.edis的操作管理
# @Author: liujin
# @Time: 2023/2/22 17:38
import json
import os


class MRedis:

    def __init__(self, db):
        import redis
        self.__h = '47.98.234.137'
        self.__p = 'LsyYsl19930729LsyYsl'
        self.__r = redis.Redis(host=self.__h, password=self.__p, db=db)

    def query(self, key):
        return self.__r.get(key)


if __name__ == '__main__':
    a = MRedis('1')
    res = a.query('abcqweroiu@haha.com_6')
    print(type(res))
    if isinstance(res, bytes):
        print(True)
    else:
        print(False)
    # print(int())
