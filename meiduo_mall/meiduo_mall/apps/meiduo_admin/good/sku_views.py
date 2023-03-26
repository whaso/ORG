from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from goods.models import SKU, GoodsCategory, SPU, SPUSpecification
from meiduo_admin.good import sku_serializers
from meiduo_admin.my_paginate import MyPageNumberPagination


class SKUViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = sku_serializers.SKUSerializer
    queryset = SKU.objects.all()

    #1.重写get_queryset过滤数据
    def get_queryset(self):
        #1.获取查询关键字
        keyword = self.request.query_params.get('keyword')

        #2.判断是否有关键字
        if keyword:
            return SKU.objects.filter(name__contains=keyword)
        else:
            return SKU.objects.order_by("id").all()


class SKUCategoryView(ListAPIView):
    serializer_class = sku_serializers.SKUCategorySerializer
    queryset = GoodsCategory.objects.filter(subs__isnull=True)


class SKUSPUSimpleView(ListAPIView):
    serializer_class = sku_serializers.SKUSPUSimpleSerializer
    queryset = SPU.objects.all()


class SPUSpecificationView(ListAPIView):
    serializer_class = sku_serializers.SPUSpecificationSerializer

    def get_queryset(self):

        spu_id = self.kwargs.get('spu_id')

        return SPUSpecification.objects.filter(spu_id=spu_id)
