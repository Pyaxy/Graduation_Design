import logging
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from ..serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshPairSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response(
        {
            "user_id": request.user.user_id,
            "name": request.user.name,
        }
    )


# 自定义的刷新视图
class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshPairSerializer


# 用户登录接口
class LoginView(TokenObtainPairView):
    # 自定义的序列化生成器
    """
    用户登录接口
    post example:
    {
        "email": "user@emample.com",
        "password": "password",
    }
    payload example:
    {
    "refresh": "eyJhbGciOiJIUz...",
    "access": "eyJhbGciOiJIU...",
    "user_id": "admin...",
    "role": "管理员",
    "name": "jack"
    }
    """

    logger = logging.getLogger(__name__)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # print("产生一个login请求！")
        response = super().post(request, *args, **kwargs)
        logger.info("产生一个login请求: {%s}" % request.data)
        if response.status_code == status.HTTP_200_OK:
            # 验证成功,生成令牌
            return Response(response.data, status=status.HTTP_200_OK)
        return Response(
            {"error": "邮箱或密码错误"}, status=status.HTTP_401_UNAUTHORIZED
        )
