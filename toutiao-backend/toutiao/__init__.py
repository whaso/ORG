from flask import Flask
from elasticsearch5 import Elasticsearch
import socketio
import grpc


def create_flask_app(config, enable_config_file=False):
    """
    创建Flask应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: Flask应用
    """
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        from utils import constants
        app.config.from_envvar(constants.GLOBAL_SETTING_ENV_NAME, silent=True)

    return app


def create_app(config, enable_config_file=False):
    """
    创建应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: 应用
    """
    app = create_flask_app(config, enable_config_file)

    # 创建Snowflake ID worker. 雪花算法
    from utils.snowflake.id_worker import IdWorker
    app.id_worker = IdWorker(app.config['DATACENTER_ID'],
                             app.config['WORKER_ID'],
                             app.config['SEQUENCE'])

    # 配置日志
    from utils.logging import create_logger
    create_logger(app)

    # 注册url转换器
    from utils.converters import register_converters
    register_converters(app)

    from redis.sentinel import Sentinel
    # 创建哨兵对象
    _sentinel = Sentinel(app.config['REDIS_SENTINELS'])
    # 配置主redis
    app.redis_master = _sentinel.master_for(app.config['REDIS_SENTINEL_SERVICE_NAME'])
    # 配置从redis
    app.redis_slave = _sentinel.slave_for(app.config['REDIS_SENTINEL_SERVICE_NAME'])

    from rediscluster import StrictRedisCluster
    # 配置redis集群
    app.redis_cluster = StrictRedisCluster(startup_nodes=app.config['REDIS_CLUSTER'])

    # rpc
    app.rpc_reco = grpc.insecure_channel(app.config['RPC'].RECOMMEND)

    # socketio
    app.sio = socketio.KombuManager(app.config['RABBITMQ'], write_only=True)

    # 创建elasticsearch对象
    app.es = Elasticsearch(
        app.config['ES'],
        # 启动前嗅探es集群服务器
        sniff_on_start=True,
        # es集群服务器结点连接异常时是否刷新es结点信息
        sniff_on_connection_fail=True,
        # 每60秒刷新结点信息
        sniffer_timeout=60
    )

    # MySQL数据库连接初始化
    from models import db
    # 使用方式二创建db对象
    db.init_app(app)

    # 注册用户模块蓝图
    from .resources.user import user_bp
    app.register_blueprint(user_bp)

    # 注册新闻模块蓝图
    from .resources.news import news_bp
    app.register_blueprint(news_bp)

    # 注册通知模块
    from .resources.notice import notice_bp
    app.register_blueprint(notice_bp)

    # 搜索
    from .resources.search import search_bp
    app.register_blueprint(search_bp)

    # 添加请求钩子
    from utils.middlewares import jwt_authentication
    app.before_request(jwt_authentication)

    return app

