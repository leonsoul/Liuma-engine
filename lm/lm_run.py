# -*- coding: utf-8 -*-
import threading
import unittest

from lm import lm_case, lm_result
from lm.lm_log import ErrorLogger


class LMRun(object):
    def __init__(self, plan_tuple, run_index, default_result, default_lock, queue):
        """
        创建用例运行类
        Parameters
        ----------
        plan_tuple：用例列表
        run_index：当前执行的次数 1为第一次，2为失败重试
        default_result： 默认的结果列表
        default_lock： 线程锁
        queue： 队列
        """
        self.plan_tuple = plan_tuple
        self.run_index = run_index
        self.default_result = default_result
        self.default_lock = default_lock
        self.queue = queue

    def run_test(self):
        suite = unittest.TestSuite()
        for case in self.plan_tuple:  # 从用例集中拿到接口用例
            cls_name = case["test_class"]
            try:
                cls = eval(cls_name)  # 执行class_name
            except:  # 如果执行失败，构造一个测试类cls，包含类名，LMCase类的值，将__doc__改为类名
                cls = type(cls_name, (lm_case.LMCase,), {'__doc__': cls_name})
            case_name = case["test_case"]
            case_type = case["test_type"]
            setattr(cls, case_name, lm_case.LMCase.testEntrance)  # 将运行入口函数赋值给case_name
            case_data = case["test_data"]  # case_data获得接口用例的信息 描述，接口用例id，导入函数，导入公参，接口列表
            # 构建测试类，将信息填入测试类中
            test_case = cls(case_name, case_data, case_type)
            test_case.task_id = case["task_id"]
            test_case.driver = case["driver"]
            test_case.session = case["session"]
            test_case.context = case["context"]
            test_case.run_index = self.run_index
            # 将任务加到suite中
            suite.addTest(test_case)

        result = lm_result.LMResult(self.default_result, self.default_lock, self.queue)

        try:
            # 使用suite执行LMResult方法，执行测试用例
            suite(result)
        except Exception as ex:
            ErrorLogger("Failed to run test(RunTime:run%s & ThreadName:%s), Error info:%s" %
                        (self.run_index, threading.current_thread().name, ex))
