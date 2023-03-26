from django.db import transaction
from rest_framework import serializers

from goods.models import SKU, GoodsCategory, SPU, SpecificationOption, SPUSpecification, SKUSpecification


class SKUSpecificationSerializer(serializers.Serializer):
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()


class SKUSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField(read_only=True)
    spu_id = serializers.IntegerField()

    category = serializers.StringRelatedField(read_only=True)
    category_id = serializers.IntegerField()

    specs = SKUSpecificationSerializer(read_only=True, many=True)

    class Meta:
        model = SKU
        fields = "__all__"
    @transaction.atomic
    def create(self, validated_data):

        sid = transaction.savepoint()  # TODO 设置保存点

        try:

            sku = SKU.objects.create(**validated_data)

            specs = self.context['request'].data['specs']
            for spec_dict in specs:
                SKUSpecification.objects.create(sku_id=sku.id, spec_id=spec_dict['spec_id'], option_id=spec_dict['option_id'])
        except Exception:
            transaction.savepoint_rollback(sid)  # TODO 回滚
            raise serializers.ValidationError('sku添加异常')
        else:
            transaction.savepoint_commit(sid)
            return sku

    @transaction.atomic
    def update(self, instance, validated_data):
        sid = transaction.savepoint()
        try:
            #1.更改sku基础信息
            SKU.objects.filter(id=instance.id).update(**validated_data)

            #2.更改规格信息
            #删除以前的规格
            [spec.delete() for spec in instance.specs.all()]

            #创建新的规格
            specs = self.context['request'].data['specs']
            for spec_dict in specs:
                SKUSpecification.objects.create(sku_id=instance.id,
                                                spec_id=spec_dict['spec_id'],
                                                option_id=spec_dict['option_id'])
        except Exception:
            transaction.savepoint_rollback(sid)
            raise serializers.ValidationError('sku修改异常')
        else:
            transaction.savepoint_commit(sid)
            return SKU.objects.get(id=instance.id)


class SKUCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = "__all__"


class SKUSPUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ('id', 'name')


class SPUSpecificationOption(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ("id", "value")


class SPUSpecificationSerializer(serializers.ModelSerializer):
    options = SPUSpecificationOption(read_only=True, many=True)

    class Meta:
        model = SPUSpecification
        fields = "__all__"

