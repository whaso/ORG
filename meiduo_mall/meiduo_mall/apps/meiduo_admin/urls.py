from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

from meiduo_admin.good import sku_views, spu_views, spu_specs_views, specs_options_views, channel_manage_views, \
    brand_manage_views, sku_image_view, sku_images_view
from meiduo_admin.sysmanage import permission_view, admin_view
from meiduo_admin.user import user_views
from meiduo_admin.home import home_views
from meiduo_admin.order import order_view

urlpatterns = [
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^statistical/total_count/$', home_views.UserTotalCountView.as_view()),
    url(r'^statistical/day_increment/$', home_views.UserDayIncrementView.as_view()),
    url(r'^statistical/day_active/$', home_views.UserDayActiveView.as_view()),
    url(r'^statistical/day_orders/$', home_views.UserDayOrdersView.as_view()),
    url(r'^statistical/month_increment/$', home_views.UserMonthIncrementCountView.as_view()),
    url(r'^statistical/goods_day_views/$', home_views.UserGoodsDayCountView.as_view()),

    url(r'^users/$', user_views.UserView.as_view()),

    url(r'^skus/categories/$', sku_views.SKUCategoryView.as_view()),
    url(r'^goods/simple/$', sku_views.SKUSPUSimpleView.as_view()),
    url(r'^goods/(?P<spu_id>\d+)/specs/$', sku_views.SPUSpecificationView.as_view()),

    url(r'^goods/brands/simple/$', spu_views.SPUBrandSimpleView.as_view()),
    url(r'^goods/channel/categories/$', spu_views.SPUCategoryView.as_view()),
    url(r'^goods/channel/categories/(?P<category_id>\d+)/$', spu_views.SPUSubsCategoryView.as_view()),

    url(r'^goods/images/$', spu_views.SPUImageUploadView.as_view()),

    url(r'^goods/specs/simple/$', specs_options_views.SpecSimpleView.as_view()),

    # get channel widget
    url(r'^goods/channel_types/$', channel_manage_views.ChannelSimpleView.as_view()),

    # get category1 widget
    url(r'^goods/categories/$', channel_manage_views.CategoriesView.as_view()),

    # sku image
    url(r'^skus/simple/$', sku_images_view.SKUSimpleView.as_view()),

    # order url list
    # url(r'^orders/$', order_view.OrderInfoView.as_view()),
    #order detail
    # url(r'^orders/(?P<pk>\d+)/$', order_view.OrderInfoDetailView.as_view()),
    # change order status
    url(r'^orders/(?P<pk>\d+)/status/$', order_view.OrderINfoReadOnlymodelViewSet.as_view({"put":"status"})),

    #permission
    url(r'^permission/simple/$', permission_view.PermissionSimpleView.as_view()),

    # permission group
    url(r'^permission/groups/simple/$', admin_view.PermissionGroupView.as_view()),
    # url(r'^permission/groups/$', admin_view.PermissionGroupView.as_view()),

]

# admin management
admin_router = DefaultRouter()
admin_router.register(r'permission/admins', admin_view.AdminManagerViewSet, base_name="admins")
urlpatterns += admin_router.urls

# permission management
permission_router = DefaultRouter()
# permission_router.register(r'permission/perms', permission_view.PermissionViewSet, base_name="permission")
permission_router.register(r'permission/groups', permission_view.PermissionViewSet, base_name="permission")
urlpatterns += permission_router.urls

# order order detail manage
order_detail_router = DefaultRouter()
order_detail_router.register(r'orders', order_view.OrderINfoReadOnlymodelViewSet, base_name="orders")
urlpatterns += order_detail_router.urls

# sku image manage
sku_image_router = DefaultRouter()
sku_image_router.register(r'skus/images', sku_image_view.SKUImageViewSet, base_name='iamges')
urlpatterns += sku_image_router.urls

# home/brands
brand_router = DefaultRouter()
brand_router.register(r'goods/brands', brand_manage_views.BrandViewSet, base_name="brands")
urlpatterns += brand_router.urls


#channel /goods/channels/ 频道管理
channel_router = DefaultRouter()
channel_router.register(r'goods/channels', channel_manage_views.ChannelManageViewSet, base_name='channels')
urlpatterns += channel_router.urls

#spec option 管理
router = DefaultRouter()
router.register(r'specs/options', specs_options_views.SpecsOptionViewSet, base_name='options')
urlpatterns += router.urls

#spu spec管理
spec_router = DefaultRouter()
spec_router.register(r'goods/specs', spu_specs_views.SPUSpecsViewSet, base_name="specs")
urlpatterns += spec_router.urls

#SPU url manager
spu_router = DefaultRouter()
spu_router.register(r'goods', spu_views.SPUViewSet, base_name="goods")
urlpatterns += spu_router.urls


# SKU url manager
sku_router = DefaultRouter()
sku_router.register(r'skus', sku_views.SKUViewSet, base_name="skus")
urlpatterns += sku_router.urls


