from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from meiduo_admin.my_paginate import MyPageNumberPagination
from meiduo_admin.order import order_serializers
from orders.models import OrderInfo


class OrderInfoView(ListAPIView):
    pagination_class = MyPageNumberPagination
    serializer_class = order_serializers.OrderInfoSerializer
    # queryset = OrderInfo.objects.order_by("order_id").all()

    def get_queryset(self):
        #1.获取关键字
        keyword = self.request.query_params.get("keyword", "")

        #2.返回数据源
        return OrderInfo.objects.filter(order_id__contains=keyword).order_by("order_id").all()


class OrderInfoDetailView(RetrieveAPIView):
    serializer_class = order_serializers.OrderInfoDetailSerializer
    queryset = OrderInfo.objects.order_by("order_id").all()


class OrderINfoReadOnlymodelViewSet(ReadOnlyModelViewSet):
    pagination_class = MyPageNumberPagination

    #1.重写获取序列化器方法
    def get_serializer_class(self):
        if self.action == "list":
            return order_serializers.OrderInfoSerializer
        else:
            return order_serializers.OrderInfoDetailSerializer

    #2.重写获取数据集方法
    def get_queryset(self):
        if self.action == "list":
            keyword = self.request.query_params.get("keyword", "")
            return OrderInfo.objects.filter(order_id__contains=keyword).order_by("order_id")
        else:
            return OrderInfo.objects.order_by("order_id")

    #3.修改订单状态
    def status(self, request, *args, **kwargs):
        #1.获取参数
        stat = request.data.get("status")
        order = self.get_object()

        #2.校验参数
        if not stat:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        #3.数据入库
        order.status = stat
        order.save()

        #
        return Response(status=status.HTTP_200_OK)
