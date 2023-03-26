from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$',views.SKUListView.as_view()),
    url(r'^hot/(?P<category_id>\d+)/$',views.HotSKUListView.as_view()),
    url(r'^detail/(?P<sku_id>\d+)/$',views.SKUDetailView.as_view()),
    url(r'^detail/visit/(?P<category_id>\d+)/$',views.CategoryVisitCountView.as_view()),
    url(r'^browse_histories/$',views.SKUBrowseHistoryView.as_view()),
    url(r'^comment/(?P<sku_id>\d+)/$', views.GetCommentView.as_view()),
]