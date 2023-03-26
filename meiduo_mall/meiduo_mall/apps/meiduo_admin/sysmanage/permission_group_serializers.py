from django.contrib.auth.models import Group, Permission
from rest_framework import serializers


class PermissionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class PermissionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"