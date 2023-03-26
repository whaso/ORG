from rest_framework.viewsets import ModelViewSet

from goods.models import SPUSpecification
from meiduo_admin.good import spu_specs_serializers
from meiduo_admin.my_paginate import MyPageNumberPagination


class SPUSpecsViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = spu_specs_serializers.SPUSpesSerializer
    queryset = SPUSpecification.objects.all()