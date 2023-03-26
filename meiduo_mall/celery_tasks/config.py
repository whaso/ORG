#1, 配置任务队列,结果队列 (可以是redis, RabbitMQ, ActiveMQ, RockerMQ, Kafka...)
broker_url = 'redis://127.0.0.1:6379/14'
result_backend = 'redis://127.0.0.1:6379/15'