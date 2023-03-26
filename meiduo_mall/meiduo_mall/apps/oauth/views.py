import json

from django.contrib.auth import login,authenticate
from django.shortcuts import render,redirect
from django.views import View
from django import http
from django.conf import settings
from QQLoginTool.QQtool import OAuthQQ
from .models import OAuthQQUser, SinaUser
from meiduo_mall.utils.my_openid import encode_openid,decode_openid
from django_redis import get_redis_connection
from users.models import User
from carts.utils import merge_cookie_redis_data
from . import sinaweibopy3

# 1,获取qq登录页面
class QQLoginView(View):
    def get(self,request):
        #1,创建qq对象
        oauth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI,
                           state='/')

        #2,获取qq登录页面
        login_url = oauth_qq.get_qq_url()

        #3,返回响应
        return http.JsonResponse({
            "login_url":login_url
        })

# 2,获取openid
class OAuthCallBackView(View):
    def get(self,request):
        #1,获取参数
        code = request.GET.get("code")

        #2,校验参数
        if not code:
            return http.HttpResponseForbidden("code丢失")

        #3,获取access_token
        oauth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI,
                           state='/')
        access_token = oauth_qq.get_access_token(code=code)

        #4,获取openid
        openid = oauth_qq.get_open_id(access_token=access_token)

        #5,通过openid,查询qq用户
        try:
            qq_user = OAuthQQUser.objects.get(open_id=openid)
        except Exception as e:
            #5,1 初次授权
            encrypt_openid = encode_openid(openid)
            context = {
                "token":encrypt_openid
            }
            #5,2 返回授权页面
            return render(request,'oauth_callback.html',context=context)
        else:
            #5,2 非初次授权,获取美多用户
            user = qq_user.user

            #5,3 状态保持
            login(request,user)

            #5,4 返回响应
            response = redirect('/')
            response.set_cookie("username",user.username)
            response = merge_cookie_redis_data(request,user,response)
            return response

    def post(self,request):
        #1,获取参数
        encry_openid = request.POST.get("access_token")
        mobile = request.POST.get("mobile")
        password = request.POST.get("pwd")
        sms_code = request.POST.get("sms_code")

        #2,校验参数
        #2,0解密openid
        openid = decode_openid(encry_openid)

        if not openid:
            return http.HttpResponseForbidden("openid过期")

        #2,1为空校验
        if not all([encry_openid,mobile,password,sms_code]):
            return http.HttpResponseForbidden("参数不全")

        #2,2校验短信验证码
        redis_conn = get_redis_connection("code")
        redis_sms_code = redis_conn.get("sms_code_%s"%mobile)

        #2,3判断短信验证码是否过期
        if not redis_sms_code:
            return http.HttpResponseForbidden("短信过期")

        #2,4判断正确性
        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden("短信错误")

        #3,数据入库
        #3,1判断账号密码正确性
        user = authenticate(request,username=mobile,password=password)

        #3,2判断用户是否存在
        if user:
            #3,3,创建qq用户对象
            qq_user = OAuthQQUser()

            #3,4 绑定美多用户和openid
            qq_user.user = user
            qq_user.open_id = openid
            qq_user.save()

            #3,5状态保持
            login(request,user)

            #3,6返回响应
            response = redirect("/")
            response.set_cookie("username",user.username)
            response = merge_cookie_redis_data(request, user, response)
            return response
        else:
            #4,1创建美多用户
            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)

            #4,2创建qq用户,并绑定
            qq_user = OAuthQQUser.objects.create(user=user,open_id=openid)

            #4,3状态保持
            login(request,user)

            #4,4 返回响应
            response = redirect("/")
            response.set_cookie("username",user.username)
            response = merge_cookie_redis_data(request, user, response)
            return response


class SinaLoginView(View):
    def get(self, request):
        #创建微博对象
        oauth_sina = sinaweibopy3.APIClient(app_key=settings.APP_KEY,
                               app_secret=settings.APP_SECRET,
                               redirect_uri=settings.REDIRECT_URL)

        #获取微博登录页面
        login_url = oauth_sina.get_authorize_url()

        return http.JsonResponse({"login_url": login_url})


class SinaCallBackView(View):
    def get(self, request):
        code = request.GET.get('code')

        if not code:
            return http.HttpResponseForbidden('code missing')

        # 创建微博对象
        oauth_sina = sinaweibopy3.APIClient(app_key=settings.APP_KEY,
                                            app_secret=settings.APP_SECRET,
                                            redirect_uri=settings.REDIRECT_URL)
        result = oauth_sina.request_access_token(code)
        access_token = result.access_token

        print('---------------------in sina accesstoken before .access_token is result', result)
        print('---------------------type result', type(result))
        print('----------------------in sina accesstoken is ', access_token)

        uid = result.uid

        try:
            sina_user = SinaUser.objects.get(uid=uid)
        except Exception:
            #初次登录
            encrypt_uid = encode_openid(uid)
            context = {
                'token': encrypt_uid
            }
            return render(request, 'oauth_callback.html', context=context)
        else:
            #非初次登录
            user = sina_user.user

            #状态保持
            login(request, user)

            #返回响应
            response = redirect('/')
            response.set_cookie('username', user.username)
            response = merge_cookie_redis_data(request, user, response)
            return response

    def post(self, request):
        # data = json.loads(request.body.decode())
        # print('--------------------------data', type(data), data)
        # password = data['password']
        # mobile = data['mobile']
        # sms_code = data['sms_code']
        # access_token = data['access_token']
        password = request.POST.get('pwd')
        sms_code = request.POST.get('sms_code')
        mobile = request.POST.get('mobile')
        access_token = request.POST.get('access_token')

        #校验参数
        uid = decode_openid(access_token)

        if not uid:
            return http.HttpResponseForbidden('uid过期')

        #为空检验
        if not all([access_token, mobile, password, sms_code]):
            return http.HttpResponseForbidden('参数不全')

        #校验短信验证码
        redis_conn = get_redis_connection('code')
        redis_sms_code = redis_conn.get('sms_code_%s' % mobile)

        #判断短信验证码是否孤傲器
        if not redis_sms_code:
            return http.HttpResponseForbidden('短息过去')

        #判断正确性
        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden('验证码错误')

        #数据入库
        #判断账号密码正确性
        user = authenticate(request, username=mobile, password=password)

        #判断用户是否存在
        if user:
            #创建微博用户对象
            sina_user = SinaUser()

            #绑定梅朵用户和uid
            sina_user = user
            sina_user.uid = uid
            sina_user.save()

            #状态保持
            login(request, user)

            #返回响应
            response = redirect('/')
            response.set_cookie('username', user.username)
            response = merge_cookie_redis_data(request, user, response)
            return response
        else:
            #创建梅朵用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

            #创建微博用户并绑定
            sina_user = SinaUser.objects.create(user = user, uid=uid)

            #状态保持
            login(request, user)

            #返回响应
            response = redirect('/')
            response.set_cookie('username', user.username)
            response = merge_cookie_redis_data(request, user, response)
            return response