# -*- coding: utf-8 -*-
import os
import configparser
import platform
import sys

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_PATH, "data")
FILE_PATH = os.path.join(BASE_PATH, "file")
LOG_PATH = os.path.join(BASE_PATH, "log")
CONFIG_PATH = os.path.join(BASE_PATH, "config", "config.ini")
IMAGE_PATH = os.path.join(BASE_PATH, "image")
BROWSER_PATH = os.path.join(BASE_PATH, "browser")


class IniReader:

    def __init__(self, config_ini=CONFIG_PATH):
        if os.path.exists(config_ini):
            self.ini_file = config_ini
        else:
            raise FileNotFoundError('文件不存在！')

    def data(self, section, option):
        config = configparser.ConfigParser()
        config.read(self.ini_file, encoding="utf-8")
        value = config.get(section, option)
        return value

    def option(self, section):
        config = configparser.ConfigParser()
        config.read(self.ini_file, encoding="utf-8")
        options = config.options(section)
        option = {}
        for key in options:
            option[key] = self.data(section, key)
        return option

    def modify(self, section, option, value):
        config = configparser.ConfigParser()
        config.read(self.ini_file, encoding="utf-8")
        config.set(section, option, value)
        config.write(open(self.ini_file, "r+", encoding="utf-8"))


class LMConfig(object):
    """"配置文件"""

    def __init__(self, path=CONFIG_PATH):
        reader = IniReader(path)
        self.url = reader.data("Platform", "url")
        self.enable_proxy = reader.data("Platform", "enable-proxy")
        self.enable_stderr = reader.data("Platform", "enable-stderr")
        self.engine = reader.data("Engine", "engine-code")
        self.secret = reader.data("Engine", "engine-secret")
        self.header = reader.option("Header")
        self.platform_proxy = reader.option("PlatformProxy")
        self.browser_opt = reader.data("WebDriver", "options")

        if self.browser_opt == "remote" or "/" in reader.data("WebDriver", "path"):
            self.browser_path = reader.data("WebDriver", "path")
        else:
            if platform.system() == 'Darwin':
                self.browser_path = os.path.join(BROWSER_PATH, reader.data("WebDriver", "path"))
            elif platform.system() == 'Windows':
                self.browser_path = os.path.join(BROWSER_PATH, reader.data("WebDriver", "windows-path"))
            elif platform.system() == 'Linux':
                self.browser_path = os.path.join(BROWSER_PATH, reader.data("WebDriver", "linux-path"))
            else:
                self.browser_path = os.path.join(BROWSER_PATH, reader.data("WebDriver", "path"))


class AlltuuConfig(object):
    """alltuu相关配置文件"""

    def __init__(self, path=CONFIG_PATH):
        reader = IniReader(path)
        self.endpoint = reader.data('Oss', 'Endpoint')
        self.bucket = reader.data('Oss', 'bucket')
        self.KeyId = reader.data('Oss', 'KeyId')
        self.KeySecret = reader.data('Oss', 'KeySecret')
        self.CDNKey = reader.data('CDN', 'private-key')
        self.host = reader.data('Mysql', 'host')
        self.user = reader.data('Mysql', 'user')
        self.pwd = reader.data('Mysql', 'password')
