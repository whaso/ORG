from django.shortcuts import render,redirect
from django.views import View
from meiduo_mall.utils.my_category import get_categories
from orders.models import OrderGoods, OrderInfo
from users.models import User
from .models import SKU,GoodsCategory,CategoryVisitCount
from django.core.paginator import Paginator
from meiduo_mall.utils.my_constants import LIST_SKU_PER_COUNT
from django import http
from meiduo_mall.utils.response_code import RETCODE
from datetime import datetime
import json
from django_redis import get_redis_connection
from meiduo_mall.utils.my_loginrequired import MyLoginRequiredMixin

#1,商品列表页面
class SKUListView(View):
    def get(self,request,category_id,page_num):

        #0,获取参数
        sort = request.GET.get("sort","default")

        #0,1判断sort的值
        if sort == "price":
            sort_field = "price"
        elif sort == "hot":
            sort_field = "sales"
        else:
            sort_field = "-create_time"

        #1,获取分类数据
        categories = get_categories()

        #2,查询分类中的所有商品
        skus = SKU.objects.filter(category_id=category_id).order_by(sort_field).all()

        #3,查询分类数据
        category = GoodsCategory.objects.get(id=category_id)

        #4,对数据进行分页
        paginate = Paginator(skus,LIST_SKU_PER_COUNT)
        page = paginate.page(page_num)
        current_page = page.number #当前页
        sku_list = page.object_list #当前页对象列表
        total_page = paginate.num_pages #总页数

        #2,拼接数据,渲染页面
        context = {
            "categories":categories,
            "skus":sku_list,
            "category":category,
            "current_page":current_page,
            "total_page":total_page,
            "sort":sort
        }

        return render(request,'list.html',context=context)

#2,获取热门商品数据
class HotSKUListView(View):
    def get(self,request,category_id):
        #1,查询热销数据
        skus = SKU.objects.filter(category_id=category_id).order_by("-sales")[:2]

        #2,数据转换了
        sku_list = []
        for sku in skus:
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":sku.price
            }
            sku_list.append(sku_dict)

        #3,返回响应
        return http.JsonResponse({
            "code":RETCODE.OK,
            "hot_sku_list":sku_list
        })

#3,获取商品详情
class SKUDetailView(View):
    def get(self,request,sku_id):

        #1,获取分类数据
        categories = get_categories()

        #2,获取面包屑数据
        sku = SKU.objects.get(id=sku_id)
        category =  sku.category

        #3,规格信息数据
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        #拼接数据,渲染页面
        context = {
            "categories":categories,
            "category":category,
            "sku":sku,
            "specs":goods_specs
        }
        return render(request,'detail.html',context=context)

#4,记录分类访问量
class CategoryVisitCountView(View):
    def post(self,request,category_id):

        #0,获取当天时间
        today = datetime.today()

        #1,查询访问量对象
        try:
            category_visit = CategoryVisitCount.objects.get(date=today, category_id=category_id)
        except Exception as e:
            category_visit = CategoryVisitCount()

        #2,数据入库
        category_visit.date = today
        category_visit.category_id = category_id
        category_visit.count += 1
        category_visit.save()

        #3,返回响应
        return http.JsonResponse({"code":RETCODE.OK},status=200)

#5,记录商品浏览历史
class SKUBrowseHistoryView(MyLoginRequiredMixin):
    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")
        user = request.user

        #2,校验参数
        if not sku_id:
            return http.JsonResponse({"code":RETCODE.NODATAERR,"errmsg":"参数不全"})

        #3,数据入库
        #3,1 去重,删除sku_id历史
        redis_conn = get_redis_connection("history")
        redis_conn.lrem("hisotry_%s"%user.id,0,sku_id)

        #3,2 添加
        redis_conn.lpush("hisotry_%s"%user.id,sku_id)

        #3,3 截取保证5个
        redis_conn.ltrim("hisotry_%s"%user.id,0,4)

        #4,返回响应
        return http.JsonResponse({"code":RETCODE.OK,"errmsg":"操作成功"})

    def get(self,request):
        #1,获取浏览历史记录
        redis_conn = get_redis_connection("history")
        sku_ids = redis_conn.lrange("hisotry_%s"%request.user.id,0,4)

        #2,数据拼接
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":sku.price,
            }
            sku_list.append(sku_dict)

        #3,返回响应
        return http.JsonResponse({"code":RETCODE.OK,"skus":sku_list})


class GetCommentView(View):
    def get(self, request, sku_id):
        # return http.JsonResponse({'a': '1'})
        #获取参数
        #1用sku_id获取所有order_id filter已评论
        ordergoods = OrderGoods.objects.filter(sku_id=sku_id, is_commented=True)
        # order_sku_id_list = []
        # for ordergood in ordergoods:
        #     order_sku_id_dict = {
        #         sku_id: ordergood.order_id,
        #     }
        #     order_sku_id_list.append(order_sku_id_dict)

        #2sku_id order_id => user_id => user.name
        #合并数据 enum username
        goods_comment_list = []
        for ordergood in ordergoods:
            goods_comment_dict = {
                'user_name': User.objects.get(id = OrderInfo.objects.get(order_id = ordergood.order_id).user_id).username,
                "user_comment": OrderGoods.objects.get(order_id=ordergood.order_id, sku_id=sku_id).comment,
            }
            goods_comment_list.append(goods_comment_dict)

        # goods_comment_list = goods_comment_dict
        return http.JsonResponse({"goods_comment_list": goods_comment_list}, status=200)
        # return http.JsonResponse({"goods_comment_list": 9999}, status=200)
