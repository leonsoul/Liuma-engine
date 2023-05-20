from tools.funclib.load_faker import CustomFaker
import time


def get_func_lib(test=None, lm_func=None, context=None, params=None):
    temp = {
        "context": context,
        "params": params
    }
    faker = CustomFaker(locale='zh_cn', package='provider', test=test, lm_func=lm_func, temp=temp)
    CustomFaker.seed(str(time.time()))
    return faker


if __name__ == '__main__':
    a_f = [{
        'code': "import datetime\ntoday = (datetime.datetime.utcnow()+datetime.timedelta(hours=8)).strftime('%m月%d日创建的闪传相册')\nsys_return(today)",
        'name': 'defalut_asd', 'params': {}}, {
        'code': "import datetime\ntoday = (datetime.datetime.utcnow()+datetime.timedelta(hours=8)).strftime('%m月%d日创建的闪传相册')\nsys_return(today)",
        'name': '创建相册的默认名称', 'params': {}}]
    print(get_func_lib(lm_func=a_f))
