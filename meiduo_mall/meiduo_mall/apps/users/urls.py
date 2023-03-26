from django.conf.urls import url
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    url(r'^register/$',views.UserRegisterView.as_view()),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$',views.UserCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.UserMobileCountView.as_view()),
    url(r'^login/$',views.UserloginView.as_view()),
    url(r'^logout/$',views.UserlogoutView.as_view()),
    # url(r'^info/$',login_required(views.UserInfoView.as_view())),
    url(r'^info/$',views.UserInfoView.as_view()),
    url(r'^emails/$',views.UserEmailView.as_view()),
    url(r'^emails/verification/$',views.UserEmailVerificationView.as_view()),
    url(r'^addresses/$',views.UserAddressView.as_view()),
    url(r'^addresses/create/$',views.UserAddressCreateView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/$',views.UserAddressUpdateView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/default/$',views.UserAddressDefaultView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/title/$',views.UserAddressTitleView.as_view()),
    url(r'^password/$',views.UserChangePasswordView.as_view()),
    url(r'^find_password/$', views.FindPassword.as_view()),

]