from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.my_paginate import MyPageNumberPagination
from goods.models import GoodsChannel, GoodsChannelGroup, GoodsCategory
from meiduo_admin.good import channel_manage_serializers


class ChannelManageViewSet(ModelViewSet):
    serializer_class = channel_manage_serializers.ChannelManageViewSerializer
    queryset = GoodsChannel.objects.order_by("id").all()
    pagination_class = MyPageNumberPagination


class ChannelSimpleView(ListAPIView):
    serializer_class = channel_manage_serializers.ChannelGroupSimpleSerializer
    queryset = GoodsChannelGroup.objects.order_by("id").all()


class CategoriesView(ListAPIView):
    serializer_class = channel_manage_serializers.CategoriesSimpleSerializer
    queryset = GoodsCategory.objects.filter(parent_id__isnull=True)

    # def get_queryset(self):
    #     pass
