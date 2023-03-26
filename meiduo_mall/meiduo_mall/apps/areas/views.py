from django.shortcuts import render
from django.views import View
from areas.models import Area
from django import http
from meiduo_mall.utils.response_code import RETCODE
from django.core.cache import cache

#1,获取省市区数据
class AreaView(View):
    def get(self,request):
        #1,获取参数
        area_id = request.GET.get("area_id")

        #2,判断是否有参数
        if area_id:

            # TODO 查询缓存,如果有直接返回
            subs = cache.get("subs_%s"%area_id)

            if subs:
                context = {
                    "code": RETCODE.OK,
                    "sub_data": {
                        "subs": subs
                    }
                }
                return http.JsonResponse(context)


            #2,1 获取子集区域信息
            area = Area.objects.get(id=area_id)
            cities = area.subs.all()

            #2,2 数据拼接
            subs_list = []
            for city in cities:
                city_dict = {
                    "id":city.id,
                    "name":city.name
                }
                subs_list.append(city_dict)

            context = {
                "code":RETCODE.OK,
                "sub_data":{
                    "subs":subs_list
                }
            }

            # TODO 缓存市的数据
            cache.set("subs_%s"%area_id,subs_list)

            #3,3返回响应
            return http.JsonResponse(context)
        else:

            #TODO 查询缓存,如果有直接返回
            province_list = cache.get("province_list")

            if province_list:
                return http.JsonResponse({
                    "code":RETCODE.OK,
                    "province_list":province_list
                })

            #3,查询所有省的数据
            provinces = Area.objects.filter(parent=None).all()

            #3,1拼接数据
            province_list = []
            for province in provinces:
                province_dict = {
                    "id":province.id,
                    "name":province.name
                }
                province_list.append(province_dict)

            context = {
                "code":RETCODE.OK,
                "province_list":province_list
            }

            #TODO 缓存省的数据
            cache.set("province_list",province_list)

            #3,2返回响应
            return http.JsonResponse(context)
