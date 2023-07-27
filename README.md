一、项目介绍<br><br>
    __browser:浏览器文件配置__<br> 
    __config:引擎环境配置__<br> 
    __core:UI接口执行__<br> 
    __lm:读取平台数据__<br> 
    __tools:基础工具__<br>
<br>
二、环境依赖<br><br>
    环境依赖: Python3.6+  Chrome以及对应的Chromedriver<br>
<br> 
三、使用步骤<br><br>
    1. git下载项目代码到本地<br> 
    2. 安装依赖包 pip3 install -r requirements.txt<br>
    3. 测试平台->引擎管理->注册引擎 保存engine-code和engine-secret<br>
    4. 将这两个字段填写到/config/config.ini文件对应处<br>
    5. 启动引擎 python3 startup.py<br>
    6. 平台引擎管理查看自己的引擎 显示在线 证明启动成功<br>
<br>
