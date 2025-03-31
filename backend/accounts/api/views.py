import logging
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from ..serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshPairSerializer,
    CurrentUserSerializer
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
    serializer_class = CurrentUserSerializer

    def handle_exception(self, exc):
        """处理认证异常"""
        if hasattr(exc, 'status_code') and exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return Response(
                {
                    "data": None,
                    "message": "未提供有效的访问令牌或令牌已过期"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().handle_exception(exc)

    def get(self, request):
        try:
            # 序列化用户数据
            serializer = self.serializer_class(request.user)
            # 打印响应体
            logger.info("current_user请求响应: {%s}" % serializer.data)
            # 返回响应体
            return Response(
                {
                    "data": serializer.data,
                    "message": "获取用户信息成功"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.info("current_user请求响应: {%s}" % e.detail)
            # 设置默认错误消息
            error_message = "获取用户信息失败"
            return Response(
                {
                    "data": None,
                    "message": error_message
                },
                status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
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
        try:
            # 获取请求体
            logger.info("refresh请求: {%s}" % request.data)
            # 调用父类方法
            response = super().post(request, *args, **kwargs)
            # 打印响应体
            logger.info("refresh请求响应: {%s}" % response.data)
            # 返回响应体
            return Response(
                {
                    "data": response.data,
                    "message": "刷新令牌成功"
                },
                status=response.status_code
            )
        except Exception as e:
            logger.info("refresh请求响应: {%s}" % e)
            # 令牌无效的异常
            if hasattr(e, 'status_code') and e.status_code == status.HTTP_401_UNAUTHORIZED:
                error_message = "刷新令牌失败"
                if hasattr(e, 'detail') and isinstance(e.detail, dict):
                    error_message = '无效的刷新令牌'
                else:
                    error_message = str(e.detail)
                return Response(
                    {
                        "data": None,
                        "message": error_message
                    },
                    status=e.status_code
                )
            # 令牌为空的异常
            if hasattr(e, 'status_code') and e.status_code == status.HTTP_400_BAD_REQUEST:
                error_message = "刷新令牌失败"
                if hasattr(e, 'detail'):
                    if isinstance(e.detail, dict) and 'refresh' in e.detail:
                        error_message = '刷新令牌不能为空'
                    else:
                        error_message = str(e.detail)
                return Response(
                    {
                        "data": None,
                        "message": error_message
                    },
                    status=e.status_code
                )
            return Response(
                {
                    "data": None,
                    "message": str(e) if str(e) else "刷新令牌失败"
                },
                status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
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
        400 Bad Request - 请提供邮箱和密码
    """

    logger = logging.getLogger(__name__)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            # 获取请求体    
            logger.info("login请求: {%s}" % request.data)
            # 调用父类方法
            response = super().post(request, *args, **kwargs)
            # 打印响应体
            logger.info("login请求响应: {%s}" % response.data)
            return Response(
                {
                    "data": response.data,
                    "message": "登录成功"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # 处理认证失败的情况
            if hasattr(e, 'status_code') and e.status_code == status.HTTP_401_UNAUTHORIZED:
                return Response(
                    {
                        "data": None,
                        "message": str(e.detail) if hasattr(e, 'detail') else "用户名或密码错误"
                    },
                    status=e.status_code
                )
            # 处理请求体缺少邮箱或密码的情况
            if hasattr(e, 'status_code') and e.status_code == status.HTTP_400_BAD_REQUEST:
                error_message = "请提供邮箱和密码"
                if hasattr(e, 'detail'):
                    if isinstance(e.detail, dict):
                        if 'email' in e.detail and 'password' in e.detail:
                            error_message = "邮箱和密码不能为空"
                        elif 'email' in e.detail:
                            error_message = "邮箱不能为空"
                        elif 'password' in e.detail:
                            error_message = "密码不能为空"
                return Response(
                    {
                        "data": None,
                        "message": error_message
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            # 处理其他异常
            return Response(
                {
                    "data": None,
                    "message": str(e) if str(e) else "登录失败"
                },
                status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
            )
