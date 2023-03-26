#1,导入包
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

#2,初始化环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

#3,创建celery对象
app = Celery('meiduo_mall')

#4,加载配置文件(任务队列,结果队列)
app.config_from_object('celery_tasks.config')

#5,注册任务
app.autodiscover_tasks(['celery_tasks.test.tasks',
                        'celery_tasks.sms.tasks',
                        'celery_tasks.email.tasks',
                        ])

# @app.task(bind=True)
# def debug_task(self):
#     import time
#     time.sleep(10)
#     print("helloworld")

# celery -A celery_tasks.main worker -l info