import eventlet

eventlet.monkey_patch()

import socketio

sio = socketio.Server(async_mode='eventlet')

app = socketio.Middleware(sio)

@sio.on('connect')
def on_connect(sid, environ):
    """
    客户端连接后执行的消息
    :param sid: 用于识别客户端的唯一id，由服务器生成
    :param environ: 是一个字典，在flask中的构建请求上下文对象的environ一样
    :return:
    """
    msg = '你好：{}'.format(sid)
    # 群发
    # sio.emit('message', msg)

    sio.emit('message', msg, room=sid)

@sio.on('disconnect')
def on_disconnect(sid):
    msg = '{} 离开了'.format(sid)
    # 群发
    sio.emit('message', msg)

# 创建socket对象，参数是一个元组（ip，port)
socket = eventlet.listen(('192.168.19.128', 8000))

eventlet.wsgi.server(socket, app)

