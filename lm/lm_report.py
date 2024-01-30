# -*- coding: utf-8 -*-
import datetime
import os
import shutil
import time

from lm.lm_api import LMApi
from lm.lm_config import DATA_PATH
from lm.lm_config import LOG_PATH
from lm.lm_log import DebugLogger, ErrorLogger

log_path = os.path.join(LOG_PATH, "engine_status.log")


class LMReport(object):
    def __init__(self, message_queue, case_result_queue):
        self.case_result_queue = case_result_queue
        self.message_queue = message_queue
        self.api = LMApi()

    # 监控结果
    def monitor_result(self):
        not_send_result = []  # 还未发送的报告
        last_send_time = datetime.datetime.now() - datetime.timedelta(
            seconds=3
        )  # 初始化上次上传报告时间
        while True:
            try:
                # 从用例队列中获得执行消息
                message = self.case_result_queue.get()
            except Exception as e:
                DebugLogger("获取执行结果报错 错误信息%s" % str(e))
            else:
                # 如果是执行时手动塞进去的报告状态，将信息写入日志中
                if isinstance(message, str):
                    if "run_all_start" in message:
                        task_id = message.split("--")[1]
                        data_type = message.split("--")[-1]
                        DebugLogger("任务执行启动 开始监听执行结果 任务id: %s" % task_id)
                    elif "run_all_stop" in message:
                        # 结束后如果还有没有发送的报告，将报告补充发送并写入日志中
                        if len(not_send_result) != 0:
                            DebugLogger(
                                "输出日志：" + str(not_send_result), file_path=log_path
                            )
                            self.api.upload_result(task_id, data_type, not_send_result)

                        self.post_stop(task_id)  # 执行结束
                        # 通知任务管理器清空当前执行任务
                        self.message_queue.put({"type": "completed", "data": task_id})
                        time.sleep(2)
                        break
                    else:  # start_run_index--n
                        # 一个接口用例执行完成
                        if len(not_send_result) != 0:
                            DebugLogger(
                                "输出日志：" + str(not_send_result), file_path=log_path
                            )
                            self.api.upload_result(task_id, data_type, not_send_result)
                            not_send_result.clear()
                        index = int(message.split("--")[-1])
                        if index > 0:
                            DebugLogger("用例有执行错误 重试执行 任务id: %s" % task_id)
                else:
                    # 如果是执行结果，上报执行结果
                    result = message
                    not_send_result.append(result)
                    current_time = datetime.datetime.now()
                    during = (current_time - last_send_time).seconds
                    """控制请求频率,执行小于3秒时在下次发送"""
                    if during < 3:
                        pass
                    else:
                        self.api.upload_result(task_id, data_type, not_send_result)
                        last_send_time = current_time
                        not_send_result.clear()

    def post_stop(self, task_id=None):
        DebugLogger("任务执行结束 调用接口通知平台 任务id: %s" % task_id)
        self.api.complete_task(task_id)
        data = os.path.join(DATA_PATH, str(task_id))
        if os.path.exists(data):
            try:
                shutil.rmtree(data)
            except Exception as e:
                ErrorLogger("删除测试数据失败 失败原因：%s 任务id: %s" % (str(e), task_id))
