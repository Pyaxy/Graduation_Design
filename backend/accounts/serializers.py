from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


# 验证时返回自定义token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # 获得基础token
        token = super().get_token(user)

        # 添加自定义字段
        token["role"] = user.role
        token["user_id"] = user.user_id
        return token

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
    def validate(self, attrs):
        data = super().validate(attrs=attrs)

        refresh = RefreshToken(attrs["refresh"])

        user = User.objects.get(pk=refresh["user_id"])

        data.update({"role": user.role, "user_id": user.user_id, "name": user.name})
        return data
