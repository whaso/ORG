from rest_framework import serializers

from goods.models import SPUSpecification


class SPUSpesSerializer(serializers.ModelSerializer):

    #重写spu
    spu = serializers.StringRelatedField(read_only=True)
    spu_id = serializers.IntegerField()

    class Meta:
        model = SPUSpecification
        fields = "__all__"