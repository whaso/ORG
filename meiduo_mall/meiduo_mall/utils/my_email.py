from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSeiralizer
from django.conf import settings
from users.models import User

#1,加密生成邮件链接
def generate_verify_url(user):

    #1,创建加密对象
    serializer = TJWSSeiralizer(secret_key=settings.SECRET_KEY,expires_in=300)

    #2,加密数据
    data = {
        "user_id":user.id,
        "email":user.email
    }
    token = serializer.dumps(data)

    #3,拼接链接
    verify_url = "%s?token=%s"%(settings.EMAIL_VERIFY_URL,token.decode())

    #4,返回链接
    return verify_url

#2,解密token
def decode_token(token):
    #1,创建解密对象
    serializer = TJWSSeiralizer(secret_key=settings.SECRET_KEY, expires_in=300)

    #2,解密token
    try:
        data = serializer.loads(token)
        user_id = data.get("user_id")
        user = User.objects.get(id=user_id)
    except Exception as e:
        return None

    #3,返回响应
    return user