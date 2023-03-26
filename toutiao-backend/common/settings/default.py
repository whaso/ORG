class DefaultConfig(object):
    """
    Flask默认配置
    """
    ERROR_404_HELP = False
    
    # 日志
    LOGGING_LEVEL = 'DEBUG'
    LOGGING_FILE_DIR = '/home/python/logs'
    LOGGING_FILE_MAX_BYTES = 300 * 1024 * 1024
    LOGGING_FILE_BACKUP = 10

    # flask-sqlalchemy使用的参数
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/toutiao'  # 数据库
    SQLALCHEMY_BINDS = {
        'bj-m1': 'mysql://root:mysql@127.0.0.1:3306/toutiao',
        'bj-s1': 'mysql://root:mysql@127.0.0.1:8306/toutiao',
        'masters': ['bj-m1'],
        'slaves': ['bj-s1'],
        'default': 'bj-m1'
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 追踪数据的修改信号
    # True 打印sql语句
    SQLALCHEMY_ECHO = True

    # redis 哨兵
    REDIS_SENTINELS = [
        ('127.0.0.1', '26380'),
        ('127.0.0.1', '26381'),
        ('127.0.0.1', '26382'),
    ]
    # 哨兵监控的集群名字
    REDIS_SENTINEL_SERVICE_NAME = 'mymaster'

    # redis 集群
    REDIS_CLUSTER = [
        {'host': '127.0.0.1', 'port': '7000'},
        {'host': '127.0.0.1', 'port': '7001'},
        {'host': '127.0.0.1', 'port': '7002'},
    ]

    # 限流服务redis
    RATELIMIT_STORAGE_URL = 'redis+sentinel://127.0.0.1:26380,127.0.0.1:26381,127.0.0.1:26382/mymaster'
    RATELIMIT_STRATEGY = 'moving-window'

    # JWT
    JWT_SECRET = 'TPmi4aLWRbyVq8zu9v82dWYW17/z+UvRnYTt4P6fAXA'
    # token的有效期
    JWT_EXPIRY_HOURS = 2
    # 刷新token的有效期
    JWT_REFRESH_DAYS = 14

    # rpc
    class RPC:
        RECOMMEND = '127.0.0.1:8888'
        CHATBOT = '127.0.0.1:9999'

    # elasticsearch 集群配置
    ES = [
        '127.0.0.1:9200'
    ]

    QINIU_ACCESS_KEY = '51DGWfSzbBws6szT3GVoZ8nMuqVVFAFV2P_StMbr'
    QINIU_SECRET_KEY = 'pAo3kBotA7PQLCuIF9Y2wCc7AfRs0MEss2-qdTbb'
    QINIU_BUCKET_NAME = 'toutiao-gz1401'
    QINIU_DOMAIN = 'http://pyguq9ykq.bkt.clouddn.com/'

    RABBITMQ = 'amqp://python:rabbitmqpwd@localhost:5672/toutiao'

    GEETEST_ID = ''
    GEETEST_KEY = ''

    # CORS 允许跨域
    CORS_ORIGINS = '*'

    # Snowflake ID Worker 参数
    DATACENTER_ID = 0
    WORKER_ID = 0
    SEQUENCE = 0

    # 与推荐系统对接的kafka
    KAFKA_SERVERS = [
        '127.0.0.1:9092'
    ]


class CeleryConfig(object):
    """
    Celery默认配置
    """
    broker_url = 'amqp://admin:rabbitmq@localhost:5672/delron'

    task_routes = {
        'sms.*': {'queue': 'sms'},
    }

    # 阿里短信服务
    DYSMS_ACCESS_KEY_ID = ''
    DYSMS_ACCESS_KEY_SECRET = ''


class MisDefaultConfig(DefaultConfig):
    # LOGGING_FILE_DIR = '/data/log'
    GEETEST_ID = ''
    GEETEST_KEY = ''
    SECRET_KEY = ''
    DEBUG = False
    IS_INIT = False
