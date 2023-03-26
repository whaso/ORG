from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^orders/settlement/$',views.OrderSettlementView.as_view()),
    url(r'^orders/commit/$',views.OrderCommitView.as_view()),
    url(r'^orders/success/$',views.OrderSuccessView.as_view()),
    url(r'^orders/info/(?P<page_num>\d+)/$',views.UserOrderInfoView.as_view()),
    url(r'^goods_judge/(?P<order_id>\d+)/$', views.GoodsJudgeView.as_view()),
    url(r'^orders/comment/$', views.SaveCommentView.as_view()),
]