from lm.lm_start import LMStart


__version__ = "1.3.0"


if __name__ == '__main__':
    print("-------------------------------------------------")
    print("当前所属版本号: %s" % __version__)
    print("测试引擎已启动")
    print("-------------------------------------------------")
    LMStart().main()
