from nonebot import get_driver
from nonebot.adapters.cqhttp import Bot as CQHTTPBot, Event as CQHTTPEvent
from nonebot_plugin_apscheduler import Scheduler
import nonebot
import os
import sys

# 导入您的药材监测模块
from herb_monitor import *

# 初始化驱动
driver = nonebot.get_driver()
driver.register_adapter("cqhttp", CQHTTPBot)

# 加载配置文件（假设您的配置文件名为 config.py）
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
import config

# 初始化 nonebot
nonebot.init()

# 注册您的药材监测模块
nonebot.load_plugin('herb_monitor')

# 启动机器人
if __name__ == "__main__":
    nonebot.run()