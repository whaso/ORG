from datetime import date, timedelta
from django.utils import timezone

from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import CategoryVisitCount
from meiduo_admin.my_paginate import MyPageNumberPagination
from meiduo_admin.home.home_serializers import UserGoodsDayCountSerializer
from users.models import User


class UserTotalCountView(APIView):
    def get(self, request):

        count = User.objects.count()

        return Response({
            "count": count
        })


class UserDayIncrementView(APIView):

    def get(self, request):

        #1.获取日增数
        today = date.today()
        count = User.objects.filter(date_joined__gte=today).count()

        return Response({
            "count": count
        })


class UserDayActiveView(APIView):
    def get(self, request):

        today = date.today()
        print('--------------today:', type(today), today)

        count = User.objects.filter(last_login__gte=today).count()

        return Response({
            "count": count
        })


class UserDayOrdersView(APIView):
    def get(self, request):

        #1.获取日下单用户数量
        today = date.today()
        count = User.objects.filter(orderinfo__create_time__gte=today).count()

        return Response({
            "count": 999
        })


class UserMonthIncrementCountView(APIView):
    def get(self, request):

        #1.获取99天前的时间
        old_date = date.today() - timedelta(days=29)
        # old_date = timezone.today() - timedelta(days=29)

        #2.遍历查询时间
        user_list = []
        for i in range(0, 30):
            current_date = old_date + timedelta(days=i)

            next_date = old_date + timedelta(days=1 + i)

            count = User.objects.filter(date_joined__gte=current_date,
                                        date_joined__lt=next_date).count()

            #添加对应日期对应新增人数
            user_list.append({
                "date": current_date,
                "count": count
            })

        return Response(user_list)


class UserGoodsDayCountView(GenericAPIView):
    serializer_class = UserGoodsDayCountSerializer

    def get_queryset(self):
        today = date.today()
        category_visits = CategoryVisitCount.objects.filter(date=today)
        return category_visits

    def get(self, request):

        #1.获取商品分类
        category_visits = self.get_queryset()

        #2.序列化器
        serializer = self.get_serializer(instance=category_visits, many=True)
        print('-------------serializer.data', serializer.data)

        return Response(serializer.data)

