from django.contrib.auth.models import Group, Permission
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from meiduo_admin.my_paginate import MyPageNumberPagination
from meiduo_admin.sysmanage import permission_group_serializers


class PermissionViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = permission_group_serializers.PermissionGroupSerializer
    queryset = Group.objects.order_by("id")


class PermissionSimpleView(ListAPIView):
    serializer_class = permission_group_serializers.PermissionSimpleSerializer
    queryset = Permission.objects.order_by("id")
