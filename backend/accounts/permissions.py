from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "STUDENT"


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "TEACHER"


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == "ADMIN" or request.user.is_staff
        )


class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == "TEACHER" or
            request.user.role == "ADMIN" or
            request.user.is_staff
        )


class RegisterPermission(permissions.BasePermission):
    """
    注册权限类
    规则：
    1. ADMIN角色不允许注册
    2. TEACHER角色需要管理员权限
    3. STUDENT角色可以注册
    """

    def has_permission(self, request, view):
        # 获取请求中的role
        role = request.data.get('role', 'STUDENT')  # 默认为STUDENT
        
        # ADMIN角色不允许注册
        if role == 'ADMIN':
            raise PermissionDenied("不允许注册管理员角色")
        
        # TEACHER角色需要管理员权限
        if role == 'TEACHER':
            if not request.user.is_authenticated:
                raise AuthenticationFailed("未提供有效的访问令牌或令牌已过期")
            if request.user.role != 'ADMIN':
                raise PermissionDenied("只有管理员可以注册教师账号")
        
        # STUDENT角色可以直接注册
        return True


class CanDeleteSubject(permissions.BasePermission):
    """检查用户是否可以删除课题"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以删除任何课题
        if request.user.role == 'ADMIN':
            return True
        # 教师只能删除自己创建的课题
        if request.user.role == 'TEACHER':
            return obj.creator == request.user
        return False
