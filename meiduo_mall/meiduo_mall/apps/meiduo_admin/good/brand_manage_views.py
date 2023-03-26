from django.conf import settings
from fdfs_client.client import Fdfs_client
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.good.brand_manage_serializers import BrandSerializer
from goods.models import Brand
from meiduo_admin.my_paginate import MyPageNumberPagination


class BrandViewSet(ModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.order_by("id").all()
    pagination_class = MyPageNumberPagination

    def create(self, request, *args, **kwargs):
        #1.获取参数
        name = request.data.get('name')
        first_letter = request.data.get('first_letter')
        # brand_id = request.data.get('brand_id')
        image = request.FILES.get("logo")

        #2.校验参数
        if not all([name, first_letter, image]):
            return Response(status=400)

        #3.数据入库
        #上传图片
        client = Fdfs_client(settings.BASE_CONFIG)
        result = client.upload_by_buffer(image.read())
        if result.get("Status") != "Upload successed.":
            return Response(status=400)

        image_url = result.get("Remote file_id")

        # 入库图片
        Brand.objects.create(name=name, first_letter=first_letter, logo=image_url)
        return Response(status=201)
