import pickle,base64
from django_redis import get_redis_connection

def merge_cookie_redis_data(request,user,response):
    """
    :param request: 为了获取cookie数据
    :param user:  为了获取redis数据
    :param response:  为了清空cookie数据
    :return:
    """
    #1,获取cookie
    cookie_cart = request.COOKIES.get("cart")

    #2 数据转换
    if not cookie_cart:
        return response

    cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

    #3 合并cookie,和redis
    redis_conn = get_redis_connection("carts")
    for sku_id, selected_count in cookie_cart_dict.items():
        redis_conn.hset("carts_%s"%user.id,sku_id,selected_count["count"])

        if selected_count["selected"]:
            redis_conn.sadd("selected_%s"%user.id,sku_id)
        else:
            redis_conn.srem("selected_%s" % user.id, sku_id)

    #4 清空cookie数据
    response.delete_cookie("cart")

    #5 返回
    return response