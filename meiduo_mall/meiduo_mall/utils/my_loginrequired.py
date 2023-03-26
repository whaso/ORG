from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

#1,用户登录类
class MyLoginRequiredMixin(LoginRequiredMixin,View):
    login_url = '/login/'
    redirect_field_name = 'next'