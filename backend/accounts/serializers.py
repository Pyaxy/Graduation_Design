from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)


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
        print("Received credentials:", attrs)  # 查看接受的凭证
        data = super().validate(attrs)
        print("Authenticated user:", self.user)
        # 添加额外相应字段
        data.update(
            {
                "user_id": self.user.user_id,
                "role": self.user.get_role_display(),
                "name": self.user.name,
            }
        )
        return data
