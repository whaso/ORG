from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from goods.models import SpecificationOption, SPUSpecification
from meiduo_admin.good import specs_options_serializers
from meiduo_admin.my_paginate import MyPageNumberPagination


class SpecsOptionViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = specs_options_serializers.SpecsOptionSerializer
    queryset = SpecificationOption.objects.all()


    pass


class SpecSimpleView(ListAPIView):
    serializer_class = specs_options_serializers.SpecSimpleSerializer

    def get_queryset(self):
        queryset = SPUSpecification.objects.all()

        for spec in queryset:
            spec.name = "%s - %s" % (spec.spu.name, spec.name)

        return queryset

