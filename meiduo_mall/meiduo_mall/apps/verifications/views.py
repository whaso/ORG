import json
import re

from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django import http
from meiduo_mall.libs.yuntongxun.sms import CCP
import random
from meiduo_mall.utils import my_constants

# 1, 图片验证码
from users.models import User


class ImageCodeView(View):
    def get(self,request,image_code_id):
        #1,生成图片验证码
        name,text,image_data = captcha.generate_captcha()

        #2,保存到redis中
        redis_conn = get_redis_connection("code")
        redis_conn.set("image_code_%s"%image_code_id,text,my_constants.IMAGE_CODE_EXPIRE)

        #3,返回图片验证码
        response = http.HttpResponse(image_data)
        response["Content-Type"] = "image/png"
        return response

# 2, 短信验证码
class SMSCodeView(View):
    def get(self,request,mobile):
        #1,获取参数
        image_code = request.GET.get("image_code")
        image_code_id = request.GET.get("image_code_id")

        #1,1获取短信标记,判断是否能发送
        redis_conn = get_redis_connection("code")
        flag = redis_conn.get("send_flag_%s"%mobile)
        if flag:
            return http.JsonResponse({"errmsg": "频繁发送短信"}, status=400)

        #2,校验参数
        #2,1 为空校验
        if not all([image_code,image_code_id]):
            return http.JsonResponse({"errmsg":"参数不全"},status=400)

        #2,2 图片验证码校验,是否过期
        redis_image_code = redis_conn.get("image_code_%s"%image_code_id)

        if not redis_image_code:
            return http.JsonResponse({"errmsg": "图片验证码已过期"}, status=400)

        # 删除图片验证码
        redis_conn.delete("image_code_%s"%image_code_id)

        # 判断正确性
        if image_code.lower() != redis_image_code.decode().lower():
            return http.JsonResponse({"errmsg": "图片验证码错误"}, status=400)

        #3,发送短信
        sms_code = "%06d" % random.randint(0, 999999)
        # ccp = CCP()
        # ccp.send_template_sms(mobile, [sms_code, 5], 1)

        #使用celery发送短信
        # from celery_tasks.sms.tasks import send_msg_code
        # send_msg_code.delay(mobile,sms_code)

        print("sms_code = %s"%sms_code )

        #3,1保存短信到redis中
        pipeline = redis_conn.pipeline() # 开启管道(事务)
        pipeline.set("sms_code_%s"%mobile,sms_code,my_constants.SMS_CODE_EXPIRY)
        pipeline.set("send_flag_%s"%mobile,"flag",my_constants.SMS_CODE_SEND_FLAG) # 设置发送标记
        pipeline.execute() # 提交管道(事务)

        #4,返回响应
        return http.JsonResponse({"code":0,"errmsg":"发送成功"})


class FirstStepView(View):
    def get(self, request, username):
        print('-------------------------------in FirstStepView.get')
        #1获取参数
        username = username
        text = request.GET.get('text')
        image_code_id = request.GET.get('image_code_id')
        #2校验参数
        #2.1为空
        if not all([username, text, image_code_id]):
            return http.JsonResponse({"e": "参数不全"}, status=400)

        #判断用户是否存在
        try:
            if re.match(r'^1[3-9]\d{9}$',username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except Exception:
            return http.JsonResponse({"e": "用户不存在"}, status=404)

        #判断图片验证码
        redis_conn = get_redis_connection('code')
        try:
            image_code_value = redis_conn.get('image_code_%s' % image_code_id).decode()
            if image_code_value.lower() == text.lower():
                json_data = {
                    "mobile": user.mobile,
                    "access_token": user.id,
                }
                response = http.JsonResponse(json_data, status=200)

                return response
            else:
                return http.JsonResponse({"errmsg": "验证码错误"}, status=400)
        except Exception:
            return http.JsonResponse({"errmsg": "验证码过期"}, status=400)


class SmsCodeView(View):
    def get(self, request):
        print('---------------in SecondStepView.get')
        user = User.objects.get(id = request.GET.get("access_token"))
        redis_conn = get_redis_connection('code')
        sms_code = "%06d" % random.randint(0, 999999)
        print('----------------------sms_code = %s' % sms_code)

        #保存短信到redis中
        pipeline = redis_conn.pipeline()
        pipeline.set('sms_code_%s' % user.mobile, sms_code, my_constants.SMS_CODE_EXPIRY)
        pipeline.execute()  #提交管道 （事务）
        return http.JsonResponse({"message": "发送成功"}, status=200)


class SecondStepView(View):
    def get(self, request, username):

        #1获取参数
        user = User.objects.get(username=username)
        sms_code = request.GET.get('sms_code')

        #校验参数
        redis_conn = get_redis_connection('code')
        sms_code_redis = redis_conn.get('sms_code_%s' % user.mobile).decode()
        print('------------------------', type(redis_conn.get('sms_code_%s' % user.mobile)))

        if sms_code == sms_code_redis:
            data = {
                "user_id": user.id,
                "access_token": user.id,
            }
            response = http.JsonResponse(data, status=200)
            return response
        else:
            return http.JsonResponse({'errmsg': "failed"}, status=400)


class ThirdStepView(View):
    def post(self, request, user_id):
        #1 get parameters
        user = User.objects.get(id=user_id)
        # password = request.POST.get('password')
        # password2 = request.POST.get('password2')
        password = json.loads(request.body)["password"]
        password2 = json.loads(request.body)['password2']
        # check password
        if not all([password, password2]):
            return http.JsonResponse({"message": "两次密码不一致"}, status=400)


        if password != password2:
            return http.JsonResponse({"message": "两次密码不一致"}, status=400)

        # save
        user.set_password(password)
        user.save()

        return http.JsonResponse({'message': "success"}, status=200)