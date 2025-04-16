from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed


# region 基础权限
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
# endregion
# region 注册权限
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
# endregion

# region 课题权限
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


class CanUpdateSubject(permissions.BasePermission):
    """检查用户是否可以更新课题"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以更新任何课题
        if request.user.role == 'ADMIN':
            return True
        # 教师只能更新自己创建的课题
        if request.user.role == 'TEACHER':
            return obj.creator == request.user
        return False
# endregion

# region 课程权限
class CanDeleteCourse(permissions.BasePermission):
    """检查用户是否可以删除课程"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以删除任何课程
        if request.user.role == 'ADMIN':
            return True
        # 教师只能删除自己创建的课程
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        return False
    
class CanUpdateCourse(permissions.BasePermission):
    """检查用户是否可以更新课程"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以更新任何课程
        if request.user.role == 'ADMIN':
            return True
        # 教师只能更新自己创建的课程
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        return False

class CanLeaveCourse(permissions.BasePermission):
    """检查用户是否可以退出课程"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以让学生退出任何课程
        if request.user.role == 'ADMIN':
            return True
        # 教师可以让学生退出自己创建的课程
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        # 学生只能退出自己加入的未结束的课程
        if request.user.role == 'STUDENT':
            return request.user in obj.students.all()
        return False
    
class CanSeeStudents(permissions.BasePermission):
    """检查用户是否可以查看学生列表"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以查看任何学生的列表
        if request.user.role == 'ADMIN':
            return True
        # 教师可以查看自己创建的课程的学生列表
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        # 学生可以查看自己加入的课程的学生列表
        if request.user.role == 'STUDENT':
            return request.user in obj.students.all()
        return False
# endregion