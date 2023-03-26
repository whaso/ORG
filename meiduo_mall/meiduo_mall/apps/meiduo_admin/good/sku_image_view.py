from django.conf import settings
from fdfs_client.client import Fdfs_client
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from goods.models import SKUImage, SKU
from meiduo_admin.good import sku_images_serializers
from meiduo_admin.my_paginate import MyPageNumberPagination


class SKUImageViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = sku_images_serializers.SKUImageSerializer
    queryset = SKUImage.objects.all()

    def create(self, request, *args, **kwargs):
        # 1.获取参数
        sku_id = request.data.get("sku")
        image = request.FILES.get('image')

        #2.校验参数
        if not all([sku_id, image]):
            return Response(status=400)

        #3. 数据入库 fdfs mysql
        #上传图片
        client = Fdfs_client(settings.BASE_CONFIG)
        result = client.upload_by_buffer(image.read())
        if result.get('Status') != "Upload successed.":
            return Response(status=400)
        image_url = result.get("Remote file_id")

        #入库图片
        SKUImage.objects.create(image=image_url, sku_id=sku_id)
        SKU.objects.filter(id=sku_id, default_image_url='').update(default_image_url=image_url)

        return Response(status=201)

    def update(self, request, *args, **kwargs):

        #1.获取参数
        sku_id = request.data.get('sku')
        image = request.FILES.get('image')
        sku_image = self.get_object()

        #2.校验参数
        if not all([sku_id, image]):
            return Response(status=400)

        #3.数据入库
        #上传图片
        client = Fdfs_client(settings.BASE_CONFIG)
        result = client.upload_by_buffer(image.read())
        if result.get("Status") != "Upload successed.":
            return Response(status=400)

        image_url = result.get("Remote file_id")

        #入库图片
        SKUImage.objects.filter(id=sku_image.id).update(image=image_url, sku_id=sku_id)
        return Response(status=201)
