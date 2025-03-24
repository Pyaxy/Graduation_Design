from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from ..serializers import CustomTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    # 自定义的序列化生成器
    """
    用户登录接口
    example:
    {
        "email": "user@emample.com",
        "password": "password",
    }
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            # 验证成功,生成令牌
            return Response(response.data, status=status.HTTP_200_OK)
        return Response(
            {"error": "邮箱或密码错误"}, status=status.HTTP_401_UNAUTHORIZED
        )
