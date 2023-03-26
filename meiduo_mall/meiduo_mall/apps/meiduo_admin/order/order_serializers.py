from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class OrderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = "__all__"


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ("name", "default_image_url")


class OrderGoodsSerializer(serializers.ModelSerializer):
    sku = SKUSerializer(read_only=True)

    class Meta:
        model = OrderGoods
        fields = ("count", "price", "sku")


class OrderInfoDetailSerializer(serializers.ModelSerializer):
    skus = OrderGoodsSerializer(read_only=True, many=True)
    class Meta:

        model = OrderInfo
        fields = "__all__"


