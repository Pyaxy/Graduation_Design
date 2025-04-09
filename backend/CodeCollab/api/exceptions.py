from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from functools import wraps

# 用于存储需要标准化异常处理的视图
# standardized_views = set()

# def standardize_exceptions(view_func):
#     """
#     装饰器：标记需要标准化异常处理的视图
#     """
#     @wraps(view_func)
#     def wrapper(*args, **kwargs):
#         print("-----装饰器开始-----")
#         # 将视图函数添加到标准化视图集合中
#         standardized_views.add(view_func)
#         print(standardized_views)
#         print("-----装饰器结束-----")
#         return view_func(*args, **kwargs)
#     return wrapper

def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    将标记为需要标准化异常处理的视图的异常转换为标准格式
    标准格式：{"data": null, "message": "错误信息"}
    """
    print("\n-----异常处理器开始-----")
    print(f"异常类型: {type(exc)}")
    print(f"异常信息: {str(exc)}")
    print(f"上下文: {context}")
    
    # 调用默认的异常处理器
    response = exception_handler(exc, context)
    print(f"默认处理器响应: {response}")
    
    if response is not None:
        # 获取发生错误的视图函数
        view = context.get('view')
        print(f"视图: {view}")
        view_func = getattr(view, 'action', None)
        print(f"视图函数: {view_func}")
        # print(f"标准化视图集合: {standardized_views}")

        # 将错误响应转换为标准格式
        response.data = {
                "data": None,
                "message": str(exc)
            }
        
        # # 检查是否是标记为需要标准化异常处理的视图
        # if view_func in standardized_views:
        #     print("视图在标准化集合中，进行标准化处理")
        #     # 将错误响应转换为标准格式
        #     response.data = {
        #         "data": None,
        #         "message": str(exc)
        #     }
        # else:
        #     print("视图不在标准化集合中，保持原样")
    
    print("-----异常处理器结束-----\n")
    return response 