from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^payment/(?P<order_id>\d+)/$',views.AliPaymentView.as_view()),
    url(r'^payment/status/$',views.AliOrderChangeView.as_view()),
]