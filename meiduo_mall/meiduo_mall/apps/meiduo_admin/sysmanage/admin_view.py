from django.contrib.auth.models import Group
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from meiduo_admin.my_paginate import MyPageNumberPagination
from meiduo_admin.sysmanage import admin_serializers
from users.models import User


class AdminManagerViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = admin_serializers.AdminManagerSerializer
    queryset = User.objects.filter(is_staff=True, is_superuser=True).order_by("id")


class PermissionGroupView(ListAPIView):
    serializer_class = admin_serializers.PermissionGroupSerializer
    queryset = Group.objects.all()