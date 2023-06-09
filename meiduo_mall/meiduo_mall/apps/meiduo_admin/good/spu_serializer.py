from rest_framework import serializers

from goods.models import SPU, Brand, GoodsCategory


class SPUSerializer(serializers.ModelSerializer):

    brand = serializers.StringRelatedField(read_only=True)
    brand_id = serializers.IntegerField()

    category1 = serializers.StringRelatedField(read_only=True)
    category1_id = serializers.IntegerField()
    category2 = serializers.StringRelatedField(read_only=True)
    category2_id = serializers.IntegerField()
    category3 = serializers.StringRelatedField(read_only=True)
    category3_id = serializers.IntegerField()

    class Meta:
        model = SPU
        fields = "__all__"


class SPUBrandSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name')


class SPUCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ('id', 'name')