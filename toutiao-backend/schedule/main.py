import sys
import os

# BASE_DIR：toutiao-backend的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 把toutiao-backend的绝对路径加入搜索路径
sys.path.insert(0, os.path.join(BASE_DIR))
# 把toutiao-backend/common 的绝对路径加入搜索路径
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor


# 1.定义执行器
executors = {
    # default表示默认使用进程的方式执行定时任务
    # 3表示同一时刻，最多只有3个进程同时执行
    'default': ProcessPoolExecutor(3)
}

# 2.使用上面执行器创建调度器对象，并以单独运行的方式创建.
scheduler = BlockingScheduler(executors=executors)

# 3.定义定时任务函数
from statistic import fix_statistics

# 4.添加修正统计数据任务, 使用cron指定每天凌晨3点执行
scheduler.add_job(fix_statistics, trigger='cron', hour=3)

# 立刻执行
# scheduler.add_job(fix_statistics, trigger='date')

if __name__ == '__main__':
    # 5.启动调度器
    scheduler.start()


