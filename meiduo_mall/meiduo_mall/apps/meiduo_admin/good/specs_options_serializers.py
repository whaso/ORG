from rest_framework import serializers

from goods.models import SpecificationOption, SPUSpecification


class SpecsOptionSerializer(serializers.ModelSerializer):
    spec = serializers.StringRelatedField(read_only=True)
    spec_id = serializers.IntegerField()

    class Meta:
        model = SpecificationOption
        fields = "__all__"


class SpecSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        mmodel = SPUSpecification
        fields = ('id', 'name')