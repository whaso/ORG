import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

import eventlet
eventlet.monkey_patch()

import socketio
import eventlet.wsgi

from toutiao.main import app as flask_app
from werkzeug.wrappers import Request
from utils.jwt_util import verify_jwt

if len(sys.argv) < 2:
    print('use python main.py [port].')
    exit(1)

# 从命令行获取端口
port = int(sys.argv[1])

# 创建KombuManager对象
mgr = socketio.KombuManager(flask_app.config.get('RABBITMQ'))

# 使用eventlet(协程)的方式创建socketio服务对象，并管理KombuManager对象
sio = socketio.Server(async_mode='eventlet', client_manager=mgr)

# 创建符合WSGI协议的app对象
app = socketio.Middleware(sio)


def check_user_id_from_querystring(environ, secret):
    """
    检查用户id
    :param environ:
    :param secret:
    :return: user_id or None
    """
    # 使用Request把environ转成request对象，之后的用法，跟在flask中的request请求上下文对象一样
    request = Request(environ)
    token = request.args.get('token')
    # 判断用户身份
    if token:
        payload = verify_jwt(token, secret=secret)
        if payload:
            user_id = payload.get('user_id')
            return user_id

    return None


@sio.on('connect')
def on_connect(sid, environ):
    """
    上线时
    :param sid:
    :param environ: WSGI dict
    :return:
    """

    user_id = check_user_id_from_querystring(environ, flask_app.config.get('JWT_SECRET'))
    print(user_id)

    if user_id:
        # 把用户sid添加到user_id这个房间，之后就可以使用user_id这个房间给用户发送消息了。
        sio.send('你好: {}'.format(user_id), room=sid)
        sio.enter_room(sid, str(user_id))


@sio.on('disconnect')
def on_disconnect(sid):
    """
    下线时
    :param sid:
    :return:
    """
    # 退出所有房间
    rooms = sio.rooms(sid)
    for room in rooms:
        sio.leave_room(sid, room)


@sio.on('message')
def on_message(sid, data):
    """
    和用户聊天的是机器人聊天服务，这块的内容是后面深度学习，属于自然语言处理部分。
    所以这里我们只是简单实现回复即可，后面学完深度学习再接上rpc调用。
    :param sid:
    :param data:
    :return:
    """
    ret_data = {
        'msg': '我已经收到您的消息: {}. 稍后给您回复。'.format(data)
    }
    sio.send(ret_data, room=sid)


socket = eventlet.listen(('127.0.0.1', port))

eventlet.wsgi.server(socket, app)

