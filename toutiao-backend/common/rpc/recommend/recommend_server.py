import user_reco_pb2
import user_reco_pb2_grpc
import grpc
import time
from concurrent.futures import ThreadPoolExecutor

# rpc接口定义中服务对应成Python的类
class UserRecommendService(user_reco_pb2_grpc.UserRecommendServicer):

    # 在接口定义的同名方法中补全，被调用时应该执行的逻辑
    def user_recommend(self, request, context):
        # request是调用的请求数据对象
        user_id = request.user_id
        channel_id = request.channel_id
        article_num = request.article_num
        time_stamp = request.time_stamp

        response = user_reco_pb2.Track()
        response.exposure = 'exposure param'
        response.time_stamp = round(time.time()*1000)
        recommends = []
        for i in range(article_num):
            param1 = user_reco_pb2.param1()
            param1.params.click = 'click param {}'.format(i+1)
            param1.params.collect = 'collect param {}'.format(i+1)
            param1.params.share = 'share param {}'.format(i+1)
            param1.params.read = 'read param {}'.format(i+1)
            param1.article_id = i+1
            recommends.append(param1)
        response.recommends.extend(recommends)

        # 最终要返回一个调用结果
        return response


# 创建一个rpc服务器
server = grpc.server(ThreadPoolExecutor(max_workers=10))

# 向服务器中添加被调用的服务方法
user_reco_pb2_grpc.add_UserRecommendServicer_to_server(UserRecommendService(), server)

# 微服务器绑定ip地址和端口
server.add_insecure_port('127.0.0.1:8888')

# 启动rpc服务
server.start()

# start()不会阻塞，此处需要加上循环睡眠 防止程序退出
while True:
    time.sleep(10)
