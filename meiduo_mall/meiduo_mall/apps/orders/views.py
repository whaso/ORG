from django.shortcuts import render
from django.views import View
from meiduo_mall.utils.my_loginrequired import MyLoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
from django import http
import json
from meiduo_mall.utils.response_code import RETCODE
from .models import OrderInfo,OrderGoods
from users.models import Address
from django.utils import timezone
import random
from django.db import transaction
from django.core.paginator import Paginator
from meiduo_mall.utils.my_constants import USER_ORDER_PAGE_COUNT

#1, 订单结算
class OrderSettlementView(MyLoginRequiredMixin):
    def get(self,request):

        #1,查询用户地址
        addresses = request.user.addresses.filter(is_deleted=False).all()

        #2,获取redis中选中商品
        user = request.user
        redis_conn = get_redis_connection("carts")
        cart_dict = redis_conn.hgetall("carts_%s"%user.id)
        selected_list = redis_conn.smembers("selected_%s"%user.id)

        #3,数据拼接
        sku_list = []
        total_count = 0 #总数量
        total_amount = Decimal(0.0) #总金额
        for sku_id in selected_list:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":str(sku.price),
                "count":int(cart_dict[sku_id]),
                "amount":str(int(cart_dict[sku_id]) * sku.price)
            }
            sku_list.append(sku_dict)

            #累加总数量,总金额
            total_count += int(cart_dict[sku_id])
            total_amount += (int(cart_dict[sku_id]) * sku.price)

        #4,运费, 实付款
        freight = Decimal(10.0)
        payment_amount = total_amount + freight

        #携带数据,渲染页面
        context = {
            "addresses":addresses,
            "skus":sku_list,
            "total_count":total_count,
            "total_amount":total_amount,
            "freight":str(freight),
            "payment_amount":str(payment_amount),
        }
        return render(request,'place_order.html',context=context)

#2, 订单提交
class OrderCommitView(MyLoginRequiredMixin):

    @transaction.atomic
    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        address_id = dict_data.get("address_id")
        pay_method = dict_data.get("pay_method")

        #2,校验参数
        #2,1 为空校验
        if not all([address_id,pay_method]):
            return http.JsonResponse({"code":RETCODE.NODATAERR,"errmsg":"参数不全"})

        #2,2 地址是否存在
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "地址不存在"})

        #2,3 支付方式校验
        try:
            pay_method = int(pay_method)
        except Exception as e:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "支付类型错误"})

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"],OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "支付方式有误"})

        #3,数据入库
        #3,1 订单编号
        user = request.user
        order_id = timezone.now().strftime("%Y%m%d%H%M%S") + "%09d%s"%(random.randint(0,999999999),user.id)

        #3,2 订单状态
        if pay_method == OrderInfo.PAY_METHODS_ENUM["CASH"]:
            status = OrderInfo.ORDER_STATUS_ENUM["UNSEND"]
        else:
            status = OrderInfo.ORDER_STATUS_ENUM["UNPAID"]

        #TODO 设置保存点
        sid = transaction.savepoint()

        order_info = OrderInfo.objects.create(
            order_id=order_id,
            user = request.user,
            address = address,
            total_count=0,
            total_amount=Decimal(0.0),
            freight=Decimal(10.0),
            pay_method =pay_method,
            status = status
        )

        #3,3 获取redis中需要结算的商品
        redis_conn = get_redis_connection("carts")
        cart_dict = redis_conn.hgetall("carts_%s"%user.id)
        selected_list = redis_conn.smembers("selected_%s"%user.id)

        #4 遍历,创建订单商品数据
        for sku_id in selected_list:
            while True:
                #4.1 获取sku对象,数量
                sku = SKU.objects.get(id=sku_id)
                count = int(cart_dict[sku_id])

                #4,2 判断库存是否充足
                if count > sku.stock:
                    transaction.savepoint_rollback(sid) #TODO 回滚
                    return http.JsonResponse({"code":RETCODE.NODATAERR,"errmsg":"库存不足"})

                #TODO 模拟并发下单
                # import time
                # time.sleep(5)


                #4,3 减少库存,增加销量
                # sku.stock -= count
                # sku.sales += count
                # sku.save()

                # TODO 使用乐观锁解决并发下单问题
                # 准备数据
                old_stock = sku.stock
                old_sales = sku.sales
                new_stock = old_stock - count
                new_sales = old_sales + count

                ret = SKU.objects.filter(id=sku_id,stock=old_stock).update(stock=new_stock,sales=new_sales)

                if ret == 0:
                    # transaction.savepoint_rollback(sid)  # TODO 回滚
                    # return http.JsonResponse({"code": RETCODE.NODATAERR, "errmsg": "下单失败"})
                    continue

                #4,4 创建订单商品对象
                OrderGoods.objects.create(
                    order=order_info,
                    sku=sku,
                    count=count,
                    price=sku.price
                )

                #4,5 累加数量,和价格到订单信息表
                order_info.total_count += count
                order_info.total_amount += int(count * sku.price)

                #TODO 一定要退出
                break

        #5,保存订单信息表
        order_info.save()
        transaction.savepoint_commit(sid) #TODO 提交

        #6,清空redis
        try:
            redis_conn.hdel("carts_%s" % user.id, *selected_list)
            redis_conn.srem("selected_%s" % user.id, *selected_list)
        except Exception as e:
            return http.JsonResponse({"code":RETCODE.DBERR,"errmsg":"购物车清空失败"})

        #7,返回响应
        return http.JsonResponse({"code":RETCODE.OK,"errmsg":"下单成功","order_id":order_id})

#3, 下单成功页面
class OrderSuccessView(View):
    def get(self,request):
        #1,获取参数
        order_id = request.GET.get("order_id")
        payment_amount = request.GET.get("payment_amount")
        pay_method = request.GET.get("pay_method")

        #2,携带数据渲染页面
        context = {
            "order_id":order_id,
            "payment_amount":payment_amount,
            "pay_method":pay_method
        }
        return render(request,'order_success.html',context=context)

#4, 获取用户订单信息
class UserOrderInfoView(MyLoginRequiredMixin):
    def get(self,request,page_num):
        #1,获取用户订单
        # orders = OrderInfo.objects.filter(user_id=request.user.id).order_by("order_id")
        orders = request.user.orderinfo_set.order_by("order_id")

        #1,1 给所有的order添加paymethod_name 以及 status_name
        for order in orders:
            order.paymethod_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method - 1][1]
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status-1][1]

        #2,将订单数据进行分页
        paginate = Paginator(orders,USER_ORDER_PAGE_COUNT)
        page = paginate.page(page_num)
        object_list = page.object_list #当前页对象列表
        current_page = page.number #当前页
        total_page = paginate.num_pages #总页数

        #2,拼接数据,渲染页面
        context = {
            "orders":object_list,
            "current_page":current_page,
            "total_page":total_page
        }
        return render(request,'user_center_order.html',context=context)


class GoodsJudgeView(MyLoginRequiredMixin):
    def get(self, request, order_id):
        order = OrderInfo.objects.get(order_id=order_id)
        skus = order.skus.all()
        sku_list = []
        for sku in skus:
            sku_dict = {
                "default_image_url": sku.sku.default_image_url.url,
                "name": sku.sku.name,
                "price": str(sku.price),
                "order_id": str(order_id),
                "sku_id": str(sku.sku_id)
            }
            sku_list.append(sku_dict)

        context = {
            "skus": sku_list
        }

        return render(request, 'goods_judge.html', context=context)


class SaveCommentView(MyLoginRequiredMixin):
    def post(self, request):
        #1.获取参数
        dict_data = json.loads(request.body)

        order_id = dict_data["order_id"]
        sku_id = dict_data['sku_id']
        comment = dict_data['comment']
        score = dict_data['score']
        is_anonymous = dict_data['is_anonymous']

        #数据校验
        if not all([order_id, sku_id, comment, score]):
            return http.JsonResponse({'errmsg': "数据不全"}, status=400)

        #2数据入库
        #获取模型对象
        ordergood = OrderGoods.objects.filter(order_id=order_id).get(sku_id=sku_id)
        orderinfo = OrderInfo.objects.get(order_id=order_id)

        #添加数据
        ordergood.comment = comment
        ordergood.score = score
        ordergood.is_anonymous = is_anonymous
        ordergood.is_commented = True
        ordergood.save()
        if all([ordergood.is_commented for ordergood in OrderGoods.objects.filter(order_id=order_id)]):
            orderinfo.status = 5
            orderinfo.save()

        return http.JsonResponse({'code': 0}, status=200)
