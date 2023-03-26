from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render,redirect
from django.views import View
import re
from django.http import HttpResponseForbidden
from users.models import User
from django import http
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from meiduo_mall.utils.my_loginrequired import MyLoginRequiredMixin
import json
from django.core.mail import send_mail
from django.conf import settings
from meiduo_mall.utils.my_email import generate_verify_url,decode_token
from meiduo_mall.utils import my_constants
from meiduo_mall.utils.response_code import RETCODE
from .models import Address
from carts.utils import merge_cookie_redis_data

# 1,注册类视图
class UserRegisterView(View):
    def get(self,request):
        return render(request,'register.html')

    def post(self,request):
        #1,获取参数
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        repassword = request.POST.get("cpwd")
        phone = request.POST.get("phone")
        msg_code = request.POST.get("msg_code")
        allow = request.POST.get("allow")

        #2,校验参数
        # 2,1校验用户名格式
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return HttpResponseForbidden("用户名格式有误")

        # 2,2密码格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseForbidden("用户名格式有误")

        # 2,3两次密码一致性
        if password != repassword:
            return HttpResponseForbidden("两次密码不一致")

        # 2,4手机号格式
        if not re.match(r'^1[3-9]\d{9}$',phone):
            return HttpResponseForbidden("手机号格式有误")

        # 2,5短信验证码正确性
        redis_conn = get_redis_connection("code")
        redis_sms_code = redis_conn.get("sms_code_%s"%phone)

        # 2,5,1 判断短信验证码是否过期
        if not redis_sms_code:
            return HttpResponseForbidden("短信验证码已过期")

        # 2,5,2 判断正确性
        if msg_code != redis_sms_code.decode():
            return HttpResponseForbidden("短信验证码错误")

        # 2,6是否同意协议
        if allow != 'on':
            return HttpResponseForbidden("必须同意协议")

        #3,数据入库
        User.objects.create_user(username=username,password=password,mobile=phone)

        #4,返回响应
        return redirect('/')

# 2,判断用户名是否存在
class UserCountView(View):
    def get(self,request,username):
        #1,根据username查询用户数量
        count = User.objects.filter(username=username).count()

        #2,返回响应
        return http.JsonResponse({
            "count":count
        })

# 3,判断手机号是否存在
class UserMobileCountView(View):
    def get(self,request,mobile):
        #1,根据手机号查询用户数量
        count = User.objects.filter(mobile=mobile).count()

        #2,返回响应
        return http.JsonResponse({
            "count":count
        })

# 4,用户登录
class UserloginView(View):
    def get(self,request):
        return render(request,'login.html')

    def post(self,request):
        #1,获取参数
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        remembered = request.POST.get("remembered")

        #2,校验参数
        #2,1 为空校验
        if not all([username,password]):
            return http.HttpResponseForbidden("参数不全")

        #2,2 用户名格式校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return http.HttpResponseForbidden("用户名格式错误")

        #2,3 密码格式校验
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return http.HttpResponseForbidden("密码格式错误")

        #2,4 账号密码的校验,校验成功返回用户对象,不成功返回None
        user = authenticate(request,username=username,password=password)

        if not user:
            return http.HttpResponseForbidden("用户名或者密码错误")

        #3,状态保持
        login(request, user) #在reqeust身上添加一个user属性,方便以后获取user数据
        response = redirect('/')
        if remembered == "on":
            request.session.set_expiry(my_constants.SESSIOIN_MAX_AGE)
            response.set_cookie("username",user.username,my_constants.SESSIOIN_MAX_AGE)
        else:
            response.set_cookie("username", user.username)

        #4,重定向到首页
        response = merge_cookie_redis_data(request,user,response)
        return response

# 5,退出登录
class UserlogoutView(View):
    def get(self,request):
        #1,清空cookie,session
        response = redirect('/')
        response.delete_cookie("username") #删除cookie
        # request.session.fluxsh() #清除session

        #2,清除request中的user
        logout(request)

        #3,重定向到首页
        return response

# 6,用户中心
class UserInfoView(MyLoginRequiredMixin):

    def get(self,request):
        #1,准备数据
        context = {
            "username":request.user.username,
            "mobile":request.user.mobile,
            "email":request.user.email,
            "email_active":request.user.email_active
        }

        #2,渲染页面
        return render(request, 'user_center_info.html',context=context)

# 7,用户邮箱
class UserEmailView(MyLoginRequiredMixin):
    def put(self,request):
        #1,获取参数
        data  = request.body.decode()
        dict_data = json.loads(data)
        email = dict_data.get("email")

        #2,校验参数
        if not email:
            return http.JsonResponse({"errmsg":"参数不全","code":RETCODE.NODATAERR})

        #3,发送邮件,数据入库
        request.user.email = email
        request.user.save()

        verify_url = generate_verify_url(request.user)
        # send_mail(subject="美多商城激活链接",message=verify_url,from_email=settings.EMAIL_FROM,recipient_list=[email])
        from celery_tasks.email.tasks import send_email_url
        send_email_url.delay(verify_url,email)

        #4,返回响应
        return http.JsonResponse({"errmsg": "设置成功", "code": RETCODE.OK})

# 8,激活邮箱
class UserEmailVerificationView(View):

    def get(self,request):
        #1,获取参数
        token = request.GET.get("token")

        #2,校验参数
        #2,1为空校验
        if not token:
            return http.HttpResponseForbidden("token丢失")

        #2,2解密token
        user = decode_token(token)

        if not user:
            return http.HttpResponseForbidden("token失效了,重发邮件")

        #3,数据入库
        user.email_active = True
        user.save()

        #4,返回响应
        return http.HttpResponse("恭喜邮箱激活成功")

# 9,获取收货地址页面
class UserAddressView(MyLoginRequiredMixin):
    def get(self,request):
        #1,获取数据
        # Address.objects.filter(user_id=request.user.id).all()
        addresses = request.user.addresses.filter(is_deleted=False).all()

        #2,拼接数据
        address_list = []
        for address in addresses:
            address_dict = {
                "id":address.id,
                "title":address.title,
                "receiver":address.receiver,
                "province":address.province.name,
                "city":address.city.name,
                "district":address.district.name,
                "place":address.place,
                "mobile":address.mobile,
                "tel":address.tel,
                "email":address.email,
                "province_id":address.province_id,
                "city_id":address.city_id,
                "district_id":address.district_id,
            }
            address_list.append(address_dict)

        #3,渲染页面
        context = {
            "addresses":address_list,
            "user":request.user
        }
        return render(request,'user_center_site.html',context=context)

# 10,创建地址
class UserAddressCreateView(MyLoginRequiredMixin):
    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        title = dict_data.get("title")
        receiver = dict_data.get("receiver")
        province_id = dict_data.get("province_id")
        city_id = dict_data.get("city_id")
        district_id = dict_data.get("district_id")
        place = dict_data.get("place")
        mobile = dict_data.get("mobile")
        tel = dict_data.get("tel")
        email = dict_data.get("email")

        #2,校验参数(为空校验)
        if not all([title,receiver,province_id,city_id,district_id,place,mobile,tel,email]):
            return http.JsonResponse({"errmsg":"参数不全","code":RETCODE.NODATAERR})

        #3,数据入库
        dict_data['user'] = request.user
        address = Address.objects.create(**dict_data)

        address_dict = {
                "id":address.id,
                "title":address.title,
                "receiver":address.receiver,
                "province":address.province.name,
                "city":address.city.name,
                "district":address.district.name,
                "place":address.place,
                "mobile":address.mobile,
                "tel":address.tel,
                "email":address.email,
                "province_id":address.province_id,
                "city_id":address.city_id,
                "district_id":address.district_id,
        }

        #4,返回响应
        context = {
            "code":RETCODE.OK,
            "address":address_dict
        }
        return http.JsonResponse(context)

# 11,修改地址
class UserAddressUpdateView(MyLoginRequiredMixin):
    def put(self,request,address_id):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        title = dict_data.get("title")
        receiver = dict_data.get("receiver")
        province_id = dict_data.get("province_id")
        city_id = dict_data.get("city_id")
        district_id = dict_data.get("district_id")
        place = dict_data.get("place")
        mobile = dict_data.get("mobile")
        tel = dict_data.get("tel")
        email = dict_data.get("email")

        #2,参数校验(为空校验)
        if not all([title,receiver,province_id,city_id,district_id,place,mobile,tel,email]):
            return http.JsonResponse({"errmsg":"参数不全","code":RETCODE.NODATAERR})

        #3,数据入库
        address = Address.objects.get(id=address_id)
        address.title = title
        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.place = place
        address.mobile = mobile
        address.tel = tel
        address.email = email
        address.save()

        #4,返回响应
        address_dict = {
                "id":address.id,
                "title":address.title,
                "receiver":address.receiver,
                "province":address.province.name,
                "city":address.city.name,
                "district":address.district.name,
                "place":address.place,
                "mobile":address.mobile,
                "tel":address.tel,
                "email":address.email,
                "province_id":address.province_id,
                "city_id":address.city_id,
                "district_id":address.district_id,
        }

        context = {
            "code":RETCODE.OK,
            "address":address_dict
        }
        return http.JsonResponse(context)

    def delete(self,request,address_id):
        #1,删除地址
        address = Address.objects.get(id=address_id)
        address.is_deleted = True
        address.save()

        #2,返回响应
        return http.JsonResponse({
            "code":RETCODE.OK
        })

# 12,默认地址
class UserAddressDefaultView(MyLoginRequiredMixin):
    def put(self,request,address_id):
        #1,设置默认地址
        request.user.default_address_id = address_id

        #2,数据入库
        request.user.save()

        #3,返回响应
        return http.JsonResponse({
            "code":RETCODE.OK
        })

# 13,修改地址标题
class UserAddressTitleView(MyLoginRequiredMixin):
    def put(self,request,address_id):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        title = dict_data.get("title")

        #2,校验参数
        if not title:
            return http.JsonResponse({"errmsg":"参数不全","code":RETCODE.NODATAERR})

        #3,数据入库
        # address = Address.objects.get(id=address_id)
        # address.title = title
        # address.save()

        Address.objects.filter(id=address_id).update(title=title) #和上面三句话等价

        #4,返回响应
        return http.JsonResponse({
            "code":RETCODE.OK
        })

# 14,密码修改
class UserChangePasswordView(MyLoginRequiredMixin):

    def get(self,request):
        return render(request,'user_center_pass.html')

    def post(self,request):
        #1,获取参数
        old_pwd = request.POST.get("old_pwd")
        new_pwd = request.POST.get("new_pwd")
        new_cpwd = request.POST.get("new_cpwd")

        #2,校验参数
        #2,1 为空校验
        if not all([old_pwd,new_pwd,new_cpwd]):
            return render(request,'user_center_pass.html')

        #2,2 两次新密码是否一致
        if new_cpwd != new_pwd:
            return render(request, 'user_center_pass.html')

        #2,3 新老密码是否一样
        if old_pwd == new_pwd:
            return render(request, 'user_center_pass.html')

        #2,4 旧密码的正确性
        if not request.user.check_password(old_pwd):
            return render(request, 'user_center_pass.html')

        #3,数据入库
        request.user.set_password(new_pwd)
        request.user.save()

        #4,返回响应,重定向
        return redirect('/login')


class FindPassword(View):
    def get(self, request):
        return render(request, 'find_password.html')