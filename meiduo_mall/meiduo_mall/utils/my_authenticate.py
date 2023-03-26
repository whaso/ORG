from django.contrib.auth.backends import ModelBackend
import re
from users.models import User

#1,重写认证方法,设置多账号登录
class MyModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):

        #0, 判断用户是否是管理员
        if not request:
            #1.判断管理员是否存在
            try:
                user = User.objects.get(username=username, is_superuser=True, is_staff=True)

            except Exception:
                return None

            if user.check_password(password):
                return user

            return None
        else:
            #1,查询用户
            try:
                if re.match(r'^1[3-9]\d{9}$',username):
                    user = User.objects.get(mobile=username)
                else:
                    user = User.objects.get(username=username)
            except Exception as e:
                return None

            #2,校验密码,返回用户
            if user.check_password(password):
                return user
            else:
                return None

