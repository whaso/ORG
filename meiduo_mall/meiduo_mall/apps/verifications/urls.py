from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^image_codes/(?P<image_code_id>.+)/$',views.ImageCodeView.as_view()),
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$',views.SMSCodeView.as_view()),
    url(r'^accounts/(?P<username>.+)/sms/token/$', views.FirstStepView.as_view()),
    url(r'^sms_codes/$', views.SmsCodeView.as_view()),
    url(r'^accounts/(?P<username>.+)/password/token/$', views.SecondStepView.as_view()),
    url(r'^users/(?P<user_id>\d+)/password/', views.ThirdStepView.as_view()),
]