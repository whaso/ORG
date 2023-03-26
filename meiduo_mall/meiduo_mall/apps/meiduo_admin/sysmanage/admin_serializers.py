from django.contrib.auth.models import Group
from rest_framework import serializers

from users.models import User


class AdminManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    #1. 重写create方法， 设置管理远密码加密
    def create(self, validated_data):
        #1.创建用户对象
        user = super().create(validated_data)

        #2.设置管理员
        user.is_staff = True
        user.is_superuser = True

        #3.密码加密 入库
        user.set_password(validated_data['password'])
        user.save()

        return user

    # 重写update方法， 密码加密
    def update(self, instance, validated_data):

        #1.修改其他信息
        super().update(instance, validated_data)

        #2.修改密码
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class PermissionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"