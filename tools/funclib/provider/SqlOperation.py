# -*- coding: utf-8 -*-
# @ModuleName: SqlOperation.py
# @Function: 数据库的操作
# @Author: liujin
# @Time: 2023/4/23 18:18
from lm.lm_config import AlltuuConfig

config = AlltuuConfig()
import pymysql


class SqlOperation:
    def __init__(self):
        self.db = pymysql.connect(host=config.host, user=config.user, password=config.pwd)
        self.cur = self.db.cursor()

    def inquiry(self, sql):
        """
        数据库查询
        :param sql: eg:SELECT goods_id FROM alltuu.at_goods_sale_detail
        :return:  返回查询结果需要处理
        """
        try:
            self.cur.execute(sql)  # 执行sql语句
            results = self.cur.fetchall()  # 获取查询的所有记录
            return results
        except Exception as e:
            raise e
        finally:
            self.db.close()  # 关闭连接

    def __insert(self, sql):
        try:
            self.cur.execute(sql)
            # 提交
            self.db.commit()
        except Exception as e:
            # 错误回滚
            self.db.rollback()
        finally:
            self.db.close()

    def __update(self, sql):
        try:
            self.cur.execute(sql)  # 像sql语句传递参数
            # 提交
            self.db.commit()
        except Exception as e:
            # 错误回滚
            self.db.rollback()
        finally:
            self.db.close()

    def __delete(self, sql):
        try:
            self.cur.execute(sql)  # 像sql语句传递参数
            # 提交
            self.db.commit()
        except Exception as e:
            # 错误回滚
            self.db.rollback()
        finally:
            self.db.close()


# SQL = SqlOperation()
if __name__ == '__main__':
    sql = "SELECT goods_id FROM alltuu.at_goods_sale_detail"
    re_sql = SqlOperation().inquiry(sql)
    re = []
    for i in re_sql:
        re.append(i[0])
    print(re)
