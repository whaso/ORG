from django.shortcuts import render
from django import http
from meiduo_mall.utils.response_code import RETCODE
from django.views import View
import json
from goods.models import SKU
from django_redis import get_redis_connection
import pickle,base64
#1,操作购物车
class CartView(View):
    def post(self,request):
        """添加购物车"""
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")
        count = dict_data.get("count")
        selected = dict_data.get("selected",True)

        #2,校验参数
        #2,1校验为空
        if not all([sku_id,count]):
            return http.JsonResponse({"code":RETCODE.NODATAERR,"errmsg":"参数不全"})

        #2,2商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "商品不存在"})

        #2,3count是否是整数
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "count不是整数"})

        #2,4库存量是否足够
        if count > sku.stock:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "库存不足"})

        #3,数据入库,需要区分用户
        user = request.user
        if request.user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("carts")

            #3,2 储存用户数据到redis
            redis_conn.hincrby("carts_%s"%user.id,sku_id,count)

            if selected:
                redis_conn.sadd("selected_%s"%user.id,sku_id)

            #3,3 返回响应
            return http.JsonResponse({"code":RETCODE.OK})
        else:
            #4,1 获取cookie购物车数据
            cart_cookie = request.COOKIES.get("cart")

            #4,2 将字符串转换为字典
            cart_cookie_dict = {}
            if cart_cookie:
                cart_cookie_dict = pickle.loads(base64.b64decode(cart_cookie.encode()))

            #4,2,1 累加count
            if sku_id in cart_cookie_dict:
                old_count = cart_cookie_dict[sku_id]["count"]
                count += old_count

            #4,3 添加新的数据到字典中
            cart_cookie_dict[sku_id] = {
                "count":count,
                "selected":selected
            }

            #4,4 设置cookie返回响应
            response = http.JsonResponse({"code": RETCODE.OK})
            cart_cookie = base64.b64encode(pickle.dumps(cart_cookie_dict)).decode()
            response.set_cookie("cart",cart_cookie)
            return response

    def get(self,request):
        """获取购物车数据"""

        #1,判断用户登录状态
        user = request.user
        if request.user.is_authenticated:
            #1,获取redis数据
            redis_conn = get_redis_connection("carts")
            cart_dict = redis_conn.hgetall("carts_%s"%user.id)
            selected_list = redis_conn.smembers("selected_%s"%user.id)

            #2,拼接数据
            sku_list = []
            for sku_id in cart_dict.keys():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id":sku.id,
                    "default_image_url":sku.default_image_url.url,
                    "name":sku.name,
                    "selected":str(sku_id in selected_list),
                    "price":str(sku.price),
                    "count":int(cart_dict[sku_id]),
                    "amount":str(int(cart_dict[sku_id]) * sku.price)
                }
                sku_list.append(sku_dict)

            #3,携带数据渲染页面
            return render(request, 'cart.html',context={"sku_list":sku_list})
        else:
            #2,获取购物车数据
            cart_cookie = request.COOKIES.get("cart")

            #3,将购物车数据转字典
            cart_cookie_dict = {}
            if cart_cookie:
                cart_cookie_dict = pickle.loads(base64.b64decode(cart_cookie.encode()))

            #4,数据拼接
            sku_list = []
            for sku_id,selected_count in cart_cookie_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id": sku.id,
                    "default_image_url": sku.default_image_url.url,
                    "name": sku.name,
                    "selected": str(selected_count["selected"]),
                    "price": str(sku.price),
                    "count": int(selected_count["count"]),
                    "amount": str(int(selected_count["count"]) * sku.price)
                }
                sku_list.append(sku_dict)

            #5,渲染页面,携带数据
            return render(request, 'cart.html', context={"sku_list": sku_list})

    def put(self,request):
        # 1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")
        count = dict_data.get("count")
        selected = dict_data.get("selected", True)

        # 2,校验参数
        # 2,1校验为空
        if not all([sku_id, count]):
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "参数不全"})

        # 2,2商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "商品不存在"})

        # 2,3count是否是整数
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "count不是整数"})

        # 2,4库存量是否足够
        if count > sku.stock:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "库存不足"})

        #3,数据入库
        user = request.user
        if request.user.is_authenticated:
            #3,1获取redis对象
            redis_conn = get_redis_connection("carts")

            #3,2修改数据
            redis_conn.hset("carts_%s"%user.id,sku_id,count)

            if selected:
                redis_conn.sadd("selected_%s"%user.id,sku_id)
            else:
                redis_conn.srem("selected_%s"%user.id,sku_id)

            #3,3拼接数据
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id": sku.id,
                "default_image_url": sku.default_image_url.url,
                "name": sku.name,
                "selected": selected,
                "price": str(sku.price),
                "count": int(count),
                "amount": str(int(count) * sku.price)
            }

            #3,4返回响应
            return http.JsonResponse({"code":RETCODE.OK,"cart_sku":sku_dict})
        else:
            #4,1 获取原来的cookie数据
            cart_cookie = request.COOKIES.get("cart")

            #4,2 字符串数据转字典
            cart_cookie_dict = {}
            if cart_cookie:
                cart_cookie_dict = pickle.loads(base64.b64decode(cart_cookie.encode()))

            #4,3 设置数据
            cart_cookie_dict[sku_id] = {
                "selected":selected,
                "count":count
            }

            #4,4返回响应
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id": sku.id,
                "default_image_url": sku.default_image_url.url,
                "name": sku.name,
                "selected": selected,
                "price": str(sku.price),
                "count": int(count),
                "amount": str(int(count) * sku.price)
            }
            response = http.JsonResponse({"code":RETCODE.OK,"cart_sku":sku_dict})
            cart_cookie = base64.b64encode(pickle.dumps(cart_cookie_dict)).decode()
            response.set_cookie("cart",cart_cookie)
            return response

    def delete(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")

        #2,校验参数
        if not sku_id:
            return http.JsonResponse({"code":RETCODE.NODATAERR,"errmsg":"参数不全"})

        #3,数据入库
        user = request.user
        if request.user.is_authenticated:
            #3,1 删除redis数据
            redis_conn = get_redis_connection("carts")
            redis_conn.hdel("carts_%s"%user.id,sku_id)
            redis_conn.srem("selected_%s"%user.id,sku_id)

            #3,2 返回响应
            return http.JsonResponse({"code":RETCODE.OK})
        else:
            #4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("cart")

            #4,2 字典转换
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,3 删除数据
            if sku_id in cookie_cart_dict:
                del cookie_cart_dict[sku_id]

            #4,4 返回响应
            response = http.JsonResponse({"code":RETCODE.OK})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response.set_cookie("cart",cookie_cart)
            return response

#2,全选购物车
class CartSelectedAllView(View):
    def put(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        selected = dict_data.get("selected")

        #2,校验参数
        try:
            selected = bool(selected)
        except Exception as e:
            return http.JsonResponse({"code":RETCODE.NODATAERR,"errmsg":"参数类型有误"})

        #3,数据入库
        user = request.user
        if user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("carts")
            cart_dict = redis_conn.hgetall("carts_%s"%user.id)
            sku_ids = cart_dict.keys()

            #3,2 修改redis购物车选中数据
            if selected:
                redis_conn.sadd("selected_%s"%user.id,*sku_ids)
            else:
                redis_conn.srem("selected_%s" % user.id, *sku_ids)

            #3,3 返回响应
            return http.JsonResponse({"code":RETCODE.OK})
        else:
            #4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("cart")

            #4,2 字符串数据转字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,3 修改cookie数据
            for sku_id,selected_count in cookie_cart_dict.items():
                selected_count["selected"] = selected

            #4,4 返回响应
            response = http.JsonResponse({"code":RETCODE.OK})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response.set_cookie("cart",cookie_cart)
            return response

#3,购物车简要页面
class CartSimpleView(View):
    def get(self,request):
        #1,判断用户登录状态
        user = request.user
        if user.is_authenticated:
            # 2,获取数据
            redis_conn = get_redis_connection("carts")
            cart_dict = redis_conn.hgetall("carts_%s"%user.id)
            selected_list = redis_conn.smembers("selected_%s"%user.id)

            # 3,拼接数据
            sku_list = []
            for sku_id in cart_dict.keys():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id":sku.id,
                    "default_image_url":sku.default_image_url.url,
                    "name":sku.name,
                    "count":int(cart_dict[sku_id])
                }
                sku_list.append(sku_dict)

            # 4,返回响应
            return http.JsonResponse({"cart_skus":sku_list})
        else:
            # 5,1 获取cookie数据
            cookie_cart = request.COOKIES.get("cart")

            # 5,2 字符串转字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            # 5,3 数据转换
            sku_list = []
            for sku_id,selected_count in cookie_cart_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id": sku.id,
                    "default_image_url": sku.default_image_url.url,
                    "name": sku.name,
                    "count": int(selected_count["count"])
                }
                sku_list.append(sku_dict)

            # 5,4 返回响应
            return http.JsonResponse({"cart_skus": sku_list})

