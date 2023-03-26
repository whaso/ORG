from django.conf import settings
from fdfs_client.client import Fdfs_client
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from goods.models import SPU, Brand, GoodsCategory
from meiduo_admin.good import spu_serializer
from meiduo_admin.my_paginate import MyPageNumberPagination

class SPUViewSet(ModelViewSet):
    queryset = SPU.objects.order_by("id").all()
    serializer_class = spu_serializer.SPUSerializer
    pagination_class = MyPageNumberPagination


class SPUBrandSimpleView(ListAPIView):
    serializer_class = spu_serializer.SPUBrandSimpleSerializer
    queryset = Brand.objects.order_by('id').all()


class SPUCategoryView(ListAPIView):
    serializer_class = spu_serializer.SPUCategorySerializer
    queryset = GoodsCategory.objects.filter(parent__isnull=True)


class SPUSubsCategoryView(ListAPIView):
    serializer_class = spu_serializer.SPUCategorySerializer

    def get_queryset(self):
        category_id = self.kwargs.get("category_id")
        queryset = GoodsCategory.objects.filter(parent_id=category_id).order_by("id")
        return queryset


class SPUImageUploadView(APIView):
    def post(self, request):
        #1.获取参数
        image = request.FILES.get('image')

        #2校验参数
        if not image:

            return Response(status=400)

        #3.数据入库fdfs
        #上传图片
        client = Fdfs_client(settings.BASE_CONFIG)
        result = client.upload_by_buffer(image.read())

        #判断图片是否上传成功
        if result.get('Status') != "Upload successed.":
            return Response(status=400)
        image_url = result.get("Remote file_id")

        #返回响应
        return Response({
            "image_url": "%s %s" % (settings.BASE_URL, image_url)
        })
