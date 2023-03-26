from datetime import date, timedelta
from django.utils import timezone

from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import CategoryVisitCount
from meiduo_admin.my_paginate import MyPageNumberPagination
from meiduo_admin.user.user_serializers import UserSerializer
from users.models import User


class UserView(ListAPIView, CreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = MyPageNumberPagination
    #
    # def get(self, request):
    #     #1.获取用户
    #     users = self.get_queryset()
    #
    #     serializer = self.get_serializer(instance=users, many=True)
    #
    #     return Response({
    #         "lists": serializer.data,
    #         "page": 1,
    #         "pages": 2
    #     })
    #
    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')

        if keyword:
            return User.objects.filter(username__contains=keyword)
        else:
            return User.objects.all()

