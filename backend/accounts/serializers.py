from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from typing import Any, Dict

User = get_user_model()

# 验证时返回自定义token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    # 获取token
    @classmethod
    def get_token(cls, user):
        # 获得基础token
        token = super().get_token(user)

        # 添加自定义字段
        token["role"] = user.role
        token["user_id"] = user.user_id
        return token

    # 验证时返回自定义字段
    def validate(self, attrs):
        data = super().validate(attrs)
        # 添加额外相应字段
        data.update(
            {
                "user_id": self.user.user_id,
                "role": self.user.get_role_display(),
                "name": self.user.name,
            }
        )
        return data


class CustomTokenRefreshPairSerializer(TokenRefreshSerializer):
    """刷新token序列化器"""
    def validate(self, attrs):
        data = super().validate(attrs=attrs)

        refresh = RefreshToken(attrs["refresh"])

        user = User.objects.get(pk=refresh["user_id"])

        data.update({"role": user.role, "user_id": user.user_id, "name": user.name})
        return data


class CurrentUserSerializer(serializers.ModelSerializer):
    """当前用户信息序列化器"""
    
    class Meta:
        model = User
        fields = ['user_id', 'name', 'role']
        read_only_fields = fields


class BaseResponseSerializer(serializers.Serializer):
    """基础响应序列化器"""
    data = serializers.JSONField()
    message = serializers.CharField(default="success")

    def to_representation(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """转换为标准响应格式"""
        return {
            "data": instance.get("data", {}),
            "message": instance.get("message", "success")
        }


class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        max_length=20,
        error_messages={
            'min_length': '密码长度不能少于6个字符',
            'max_length': '密码长度不能超过20个字符'
        }
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        max_length=20,
        error_messages={
            'min_length': '确认密码长度不能少于6个字符',
            'max_length': '确认密码长度不能超过20个字符'
        }
    )
    # 默认角色为学生
    role = serializers.ChoiceField(choices=User.ROLES, default=User.ROLES[0][0])

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'user_id', 'name', 'school', 'role')
        extra_kwargs = {
            'email': {'required': True},
            'user_id': {'required': True},
            'name': {'required': True},
            'school': {'required': True}
        }

    def validate(self, attrs):
        """验证密码是否一致"""
        if attrs['password'] != attrs['confirm_password']:
            raise ValidationError("两次输入的密码不一致")
        return attrs

    def create(self, validated_data):
        """创建用户"""
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
