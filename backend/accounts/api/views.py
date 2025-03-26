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
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class CurrentUserView(APIView):
    """
    获取当前登录用户信息的接口

    请求方式: GET
    请求头:
        Authorization: Bearer <access_token>

    权限要求:
        - 需要用户已登录（携带有效的 access_token）

    响应示例:
        {
            "data": {
                "user_id": "user123",
                "name": "张三"，
                "role": "管理员"
            },
            "message": "获取用户信息成功"
        }

    错误响应:
        401 Unauthorized - 未提供有效的 access_token 或 token 已过期
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "data": {
                    "user_id": request.user.user_id,
                    "name": request.user.name,
                    "role": request.user.role,
                },
                "message": "获取用户信息成功"
            }
        )


# 自定义的刷新视图
class CustomTokenRefreshView(TokenRefreshView):
    """
    刷新 access_token 的接口

    请求方式: POST
    请求头:
        Content-Type: application/json

    请求体:
        {
            "refresh": "用户的 refresh_token"
        }

    响应示例:
        {
            "data": {
                "access": "eyJhbGciOiJIU...",
                "user_id": "admin...",
                "role": "管理员",
                "name": "jack"
            },
            "message": "刷新令牌成功"
        }

    错误响应:
        400 Bad Request - 请求参数错误
        401 Unauthorized - refresh_token 无效或已过期
        500 Internal Server Error - 服务器内部错误
    """

    serializer_class = CustomTokenRefreshPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return Response(
                {
                    "data": response.data,
                    "message": "刷新令牌成功"
                },
                status=response.status_code
            )
        return Response(
            {
                "data": None,
                "message": response.data.get("detail", "刷新令牌失败")
            },
            status=response.status_code
        )


# 用户登录接口
class LoginView(TokenObtainPairView):
    """
    用户登录接口

    请求方式: POST
    请求头:
        Content-Type: application/json

    请求体:
        {
            "email": "user@example.com",
            "password": "password"
        }

    响应示例:
        {
            "data": {
                "refresh": "eyJhbGciOiJIUz...",
                "access": "eyJhbGciOiJIU...",
                "user_id": "admin...",
                "role": "管理员",
                "name": "jack"
            },
            "message": "登录成功"
        }

    错误响应:
        401 Unauthorized - 邮箱或密码错误
    """

    logger = logging.getLogger(__name__)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        logger.info("产生一个login请求: {%s}" % request.data)
        if response.status_code == status.HTTP_200_OK:
            return Response(
                {
                    "data": response.data,
                    "message": "登录成功"
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "data": None,
                "message": response.data.get("detail", "登录失败")
            },
            status=response.status_code
        )
