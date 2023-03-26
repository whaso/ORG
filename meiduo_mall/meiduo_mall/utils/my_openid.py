from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer
from django.conf import settings

#1,加密openid
def encode_openid(openid):
    #1,创建加密对象
    serializer = TJWSSerializer(secret_key=settings.SECRET_KEY,expires_in=300)

    #2,加密openid
    token = serializer.dumps({"openid":openid})

    #3,返回加密的openid
    return token.decode()


#2,解密openid
def decode_openid(token):
    #1,创建加密对象
    serializer = TJWSSerializer(secret_key=settings.SECRET_KEY,expires_in=300)

    #2,加密openid
    try:
        data_dict = serializer.loads(token)
    except Exception as e:
        return None
    else:
        #3,返回加密的openid
        return data_dict.get("openid")
