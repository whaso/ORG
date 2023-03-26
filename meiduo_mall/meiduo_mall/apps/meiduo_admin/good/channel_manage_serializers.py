from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from goods.models import GoodsChannel, GoodsChannelGroup, GoodsCategory


class ChannelManageViewSerializer(ModelSerializer):
    group_id = serializers.PrimaryKeyRelatedField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = GoodsChannel
        fields = "__all__"


class ChannelGroupSimpleSerializer(ModelSerializer):
    class Meta:
        model = GoodsChannelGroup
        fields = "__all__"


class CategoriesSimpleSerializer(ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ("id", "name")