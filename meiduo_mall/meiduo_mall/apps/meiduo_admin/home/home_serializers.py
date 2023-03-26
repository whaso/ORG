from rest_framework import serializers

from goods.models import CategoryVisitCount
from users.models import User


class UserGoodsDayCountSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CategoryVisitCount
        fields = "__all__"
