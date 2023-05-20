from .load_faker import CustomFaker
import time


def get_func_lib(test=None, lm_func=None, context=None, params=None):
    temp = {
        "context": context,
        "params": params
    }
    faker = CustomFaker(locale='zh_cn', package='provider', test=test, lm_func=lm_func, temp=temp)
    CustomFaker.seed(str(time.time()))
    return faker

