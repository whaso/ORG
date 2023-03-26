from flask_restful import Resource
from flask import request, current_app, g
from flask_restful.reqparse import RequestParser
import random
from datetime import datetime, timedelta
from redis.exceptions import ConnectionError

from . import constants
from utils import parser
from models import db
from models.user import User, UserProfile
from utils.jwt_util import generate_jwt
from utils.decorators import set_db_to_read, set_db_to_write


class SMSVerificationCodeResource(Resource):
    """
    短信验证码
    """

    def get(self, mobile):
        code = '{:0>6d}'.format(random.randint(0, 999999))
        current_app.redis_master.setex('app:code:{}'.format(mobile), constants.SMS_VERIFICATION_CODE_EXPIRES, code)
        # 调用短信接口发送短信
        # send_verification_code.delay(mobile, code)
        return {'mobile': mobile, 'code': code}


class AuthorizationResource(Resource):
    """
    认证
    """
    method_decorators = {
        'post': [set_db_to_write],
        'put': [set_db_to_read]
    }

    def _generate_tokens(self, user_id, with_refresh_token=True):
        """
        生成token 和refresh_token
        :param user_id: 用户id
        :return: token, refresh_token
        """
        # 颁发JWT
        now = datetime.utcnow()
        # token两小时有效
        expiry = now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS'])
        token = generate_jwt({'user_id': user_id, 'refresh': False}, expiry)
        refresh_token = None
        if with_refresh_token:
            # 刷新token14天有效
            refresh_expiry = now + timedelta(days=current_app.config['JWT_REFRESH_DAYS'])
            refresh_token = generate_jwt({'user_id': user_id, 'refresh': True}, refresh_expiry)
        return token, refresh_token

    def post(self):
        """
        登录创建token
        """
        # 获取参数
        json_parser = RequestParser()
        json_parser.add_argument('mobile', type=parser.mobile, required=True, location='json')
        json_parser.add_argument('code', type=parser.regex(r'^\d{6}$'), required=True, location='json')
        args = json_parser.parse_args()
        mobile = args.mobile
        code = args.code

        # 从主redis中获取验证码
        key = 'app:code:{}'.format(mobile)
        try:
            real_code = current_app.redis_master.get(key)
        except ConnectionError as e:
            current_app.logger.error(e)
            # 如果没获取到，再在从redis中获取一次
            real_code = current_app.redis_slave.get(key)

        # 把验证码从redis中删掉
        try:
            current_app.redis_master.delete(key)
        except ConnectionError as e:
            current_app.logger.error(e)

        # 判断验证码是否正确
        if not real_code or real_code.decode() != code:
            return {'message': 'Invalid code.'}, 400

        # 查询或保存用户
        user = User.query.filter_by(mobile=mobile).first()

        if user is None:
            # 用户不存在，注册用户
            user_id = current_app.id_worker.get_id()
            user = User(id=user_id, mobile=mobile, name=mobile, last_login=datetime.now())
            db.session.add(user)
            profile = UserProfile(id=user.id)
            db.session.add(profile)
            db.session.commit()
        else:
            # 判断用户是否可用
            if user.status == User.STATUS.DISABLE:
                return {'message': 'Invalid user.'}, 403

        # 生成jwt的token和刷新token
        token, refresh_token = self._generate_tokens(user.id)
        return {'token': token, 'refresh_token': refresh_token}, 201

    def put(self):
        """
        刷新token
        """
        user_id = g.user_id
        if user_id and g.is_refresh_token:
            # 重新生成token
            token, refresh_token = self._generate_tokens(user_id, with_refresh_token=False)
            return {'token': token}, 201

        else:
            return {'message': 'Wrong refresh token.'}, 403










