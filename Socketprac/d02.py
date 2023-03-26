import eventlet
eventlet.monkey_patch()
import socketio
import eventlet.wsgi

# 创建sio对象，
sio = socketio.Server(async_mode='eventlet')

app = socketio.Middleware(sio)

#
@sio.on('connect')
def on_connect(sid, environ):
    msg = '欢迎{}来到天上众星皆拱北'.format(sid)

    sio.emit('message', msg)

@sio.on('disconnect')
def on_disconnect(sid):
    msg = '{} 离开了'.format(sid)

    sio.emit('message', msg)

@sio.on('message')
def on_message(sid, data):
    # 群发
    sio.emit('message', data, skip_sid=sid)

@sio.on('robot_chat')
def on_robot_chat(sid, data):
    sio.emit('robot_chat', data, room=sid)

socket = eventlet.listen(('192.168.19.128', 8000))

eventlet.wsgi.server(socket, app)

