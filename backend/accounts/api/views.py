import logging
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from ..serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshPairSerializer,
    CurrentUserSerializer,
    UserRegisterSerializer,
    BaseResponseSerializer
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from ..permissions import RegisterPermission
from rest_framework.exceptions import ValidationError, PermissionDenied, AuthenticationFailed

logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """基础API视图类"""
    serializer_class = BaseResponseSerializer

    def get_response(self, data=None, message='', status_code=status.HTTP_200_OK):
        """获取统一格式的响应"""
        # 直接构造响应数据，不使用序列化器
        return Response({
            'data': data,
            'message': message
        }, status=status_code)

    def handle_exception(self, exc):
        """处理异常"""
        # 获取当前视图类名，用于提供更具体的错误信息
        view_name = self.__class__.__name__
        
        if isinstance(exc, ValidationError):
            logger.info(f'{view_name} 发生了ValidationError')
            # 处理验证错误
            if isinstance(exc.detail, dict):
                # 处理字段级别的错误
                field_names = {
                    'email': '邮箱',
                    'password': '密码',
                    'confirm_password': '确认密码',
                    'user_id': '学号',
                    'name': '姓名',
                    'school': '学校',
                    'refresh': '刷新令牌'
                }
                
                # 处理刷新令牌相关错误
                if view_name == 'CustomTokenRefreshView' and 'refresh' in exc.detail:
                    return self.get_response(None, '刷新令牌不能为空或无效', status.HTTP_400_BAD_REQUEST)
                
                # 处理登录相关错误
                if view_name == 'LoginView':
                    if 'email' in exc.detail and 'password' in exc.detail:
                        return self.get_response(None, '邮箱和密码不能为空', status.HTTP_400_BAD_REQUEST)
                    elif 'email' in exc.detail:
                        return self.get_response(None, '邮箱不能为空', status.HTTP_400_BAD_REQUEST)
                    elif 'password' in exc.detail:
                        return self.get_response(None, '密码不能为空', status.HTTP_400_BAD_REQUEST)
                
                # 通用的必填字段错误处理
                missing_fields = []
                for field, errors in exc.detail.items():
                    if isinstance(errors, list):
                        for error in errors:
                            if hasattr(error, 'code') and error.code == 'required':
                                if field in field_names:
                                    missing_fields.append(field_names[field])
                                break
                
                if missing_fields:
                    error_message = f"请填写以下必填项：{', '.join(missing_fields)}"
                else:
                    # 处理其他字段错误
                    for field, errors in exc.detail.items():
                        if isinstance(errors, list):
                            error_message = str(errors[0])
                            break
                    else:
                        error_message = str(exc.detail)
            else:
                error_message = str(exc.detail)
            return self.get_response(None, error_message, status.HTTP_400_BAD_REQUEST)
        elif isinstance(exc, PermissionDenied):
            logger.info(f'{view_name} 发生了PermissionDenied')
            # 处理权限错误
            return self.get_response(None, str(exc.detail) if hasattr(exc, 'detail') else str(exc), status.HTTP_403_FORBIDDEN)
        elif isinstance(exc, AuthenticationFailed):
            logger.info(f'{view_name} 发生了AuthenticationFailed')
            # 处理认证错误
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    if 'messages' in exc.detail and isinstance(exc.detail['messages'], list):
                        error_message = str(exc.detail['messages'][0].get('message', '认证失败'))
                    else:
                        error_message = str(exc.detail.get('detail', '认证失败'))
                else:
                    # 处理ErrorDetail对象
                    error_message = str(exc.detail)
                    # 针对不同视图提供更具体的错误信息
                    if view_name == 'LoginView' and error_message == 'No active account found with the given credentials':
                        error_message = '用户名或密码错误'
                    elif view_name == 'CustomTokenRefreshView':
                        if 'token_not_valid' in str(exc):
                            error_message = '刷新令牌已过期或无效，请重新登录'
            else:
                error_message = '无效的访问令牌或令牌已过期'
            return self.get_response(None, error_message, status.HTTP_401_UNAUTHORIZED)
        elif hasattr(exc, 'status_code') and exc.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.info(f'{view_name} 发生了HTTP_401_UNAUTHORIZED')
            # 处理其他未认证错误
            error_message = '未提供有效的访问令牌或令牌已过期'
            # 针对不同视图提供更具体的错误信息
            if view_name == 'CustomTokenRefreshView':
                error_message = '刷新令牌已过期或无效，请重新登录'
            return self.get_response(None, error_message, status.HTTP_401_UNAUTHORIZED)
        # 处理其他错误
        else:
            logger.error(f'{view_name} 发生了未处理的异常: {str(exc)}')
            # 根据不同的视图提供不同的错误信息
            error_message = str(exc) if str(exc) else '服务器错误'
            if view_name == 'LoginView':
                error_message = '登录失败：' + error_message
            elif view_name == 'RegisterView':
                error_message = '注册失败：' + error_message
            elif view_name == 'CustomTokenRefreshView':
                error_message = '刷新令牌失败：' + error_message
            elif view_name == 'CurrentUserView':
                error_message = '获取用户信息失败：' + error_message
            return self.get_response(None, error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrentUserView(BaseAPIView):
    """获取当前用户信息接口"""
    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get(self, request):
        # 序列化用户数据
        serializer = self.serializer_class(request.user)
        # 打印响应体
        logger.info("current_user请求响应: {%s}" % serializer.data)
        # 返回响应体
        return self.get_response(serializer.data, "获取用户信息成功")

# 自定义的刷新视图
class CustomTokenRefreshView(TokenRefreshView, BaseAPIView):
    """刷新token接口"""
    serializer_class = CustomTokenRefreshPairSerializer

    def post(self, request, *args, **kwargs):
        # 获取请求体
        logger.info("refresh请求: {%s}" % request.data)
        # 调用父类方法
        response = super().post(request, *args, **kwargs)
        # 打印响应体
        logger.info("refresh请求响应: {%s}" % response.data)
        # 返回响应体
        return self.get_response(response.data, "刷新令牌成功")

# 用户登录接口
class LoginView(TokenObtainPairView, BaseAPIView):
    """用户登录接口"""
    logger = logging.getLogger(__name__)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # 获取请求体    
        logger.info("login请求: {%s}" % request.data)
        # 调用父类方法
        response = super().post(request, *args, **kwargs)
        # 打印响应体
        logger.info("login请求响应状态码: {%s}" % response.status_code)
        # 返回响应体
        return self.get_response(response.data, "登录成功")

class RegisterView(BaseAPIView):
    """用户注册接口"""
    permission_classes = [RegisterPermission]  # 添加权限检查
    serializer_class = UserRegisterSerializer

    def post(self, request):
        """处理注册请求"""
        # 获取请求体
        logger.info("register请求: {%s}" % request.data)
        # 验证数据
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 创建用户
        user = serializer.save()
        # 打印响应体
        logger.info("register请求响应: {%s}" % serializer.data)
        # 返回响应体
        return self.get_response(None, "注册成功", status.HTTP_201_CREATED)
