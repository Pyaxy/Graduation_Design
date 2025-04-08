import functools
import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

def standard_response(success_message=None):
    """
    装饰器，用于将视图方法的响应标准化为 {"data": ..., "message": ...} 格式
    
    参数:
        success_message: 成功时的消息，如果为None则使用默认消息
    
    用法示例：
        @standard_response("获取课题列表成功")
        def list(self, request, *args, **kwargs):
            # 原始实现...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # 获取原始响应
            response = func(self, request, *args, **kwargs)
            
            # 如果已经是标准格式，直接返回
            if isinstance(response, Response) and isinstance(response.data, dict) and 'data' in response.data and 'message' in response.data:
                return response
                
            # 确定消息
            message = success_message
            if message is None:
                # 根据请求方法和状态码生成默认消息
                if request.method == 'GET':
                    message = "获取成功"
                elif request.method == 'POST':
                    message = "创建成功"
                elif request.method == 'PUT' or request.method == 'PATCH':
                    message = "更新成功"
                elif request.method == 'DELETE':
                    message = "删除成功"
                else:
                    message = "操作成功"
            
            # 处理不同类型的响应
            if isinstance(response, Response):
                data = response.data
                status_code = response.status_code
                headers = response._headers if hasattr(response, '_headers') else {}
            else:
                data = response
                status_code = status.HTTP_200_OK
                headers = {}
                
            # 创建标准响应
            standardized_response = Response(
                {"data": data, "message": message},
                status=status_code
            )
            
            # 添加原始响应的头部
            for name, value in headers.items():
                if isinstance(value, tuple) and len(value) > 1:
                    standardized_response[name] = value[1]
                else:
                    standardized_response[name] = value
                
            return standardized_response
                
        return wrapper
    return decorator 