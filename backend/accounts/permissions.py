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
    
class CanApplyPublicSubject(permissions.BasePermission):
    """检查用户是否可以申请公开课题"""
    def has_object_permission(self, request, view, obj):
        # 教师可以申请公开自己创建的课题
        if request.user.role == 'TEACHER':
            return obj.creator == request.user
        # 管理员可以申请公开任何课题
        if request.user.role == 'ADMIN':
            return True
        return False
    
class CanReviewPublicSubject(permissions.BasePermission):
    """检查用户是否可以审核公开课题"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以审核任何公开课题
        return request.user.role == 'ADMIN'
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
    
class CanAddSubjectToCourse(permissions.BasePermission):
    """检查用户是否可以添加课题到课程"""
    
    def has_object_permission(self, request, view, obj):
        # 管理员可以添加任何课题到课程
        if request.user.role == 'ADMIN':
            return True
        # 教师可以添加自己创建的课题到课程
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        return False
    
class CanSeeSubjects(permissions.BasePermission):
    """检查用户是否可以查看课题列表"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以查看任何课题
        if request.user.role == 'ADMIN':
            return True
        # 教师可以查看自己创建的课题
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        # 学生可以查看自己加入的课程的课题列表
        if request.user.role == 'STUDENT':
            return request.user in obj.students.all()
        return False
    
class CanDeleteSubjectFromCourse(permissions.BasePermission):
    """检查用户是否可以删除课程课题"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以删除任何课程课题
        if request.user.role == 'ADMIN':
            return True
        # 教师可以删除自己创建的课程课题
        if request.user.role == 'TEACHER':
            return obj.teacher == request.user
        return False
# endregion

# region 小组权限
class CanSeeGroupDetail(permissions.BasePermission):
    """检查用户是否可以查看小组详情"""
    def has_object_permission(self, request, view, obj):
        # 管理员可以查看任何小组
        if request.user.role == 'ADMIN':
            return True
        # 教师可以查看自己创建的课程的小组
        if request.user.role == 'TEACHER':
            return obj.course.teacher == request.user
        # 学生可以查看自己加入的小组
        if request.user.role == 'STUDENT':
            return request.user in obj.students.all()
        return False
class CanJoinGroup(permissions.BasePermission):
    """检查用户是否可以加入小组"""
    def has_object_permission(self, request, view, obj):
        # 学生可以加入小组
        if request.user.role == 'STUDENT':
            return True
        return False
    
class CanLeaveGroup(permissions.BasePermission):
    """检查用户是否可以退出小组"""
    def has_object_permission(self, request, view, obj):
        # 学生可以退出自己加入的小组
        if request.user.role == 'STUDENT':
            return obj.students.filter(user_id=request.user.user_id).exists()
        # 老师可以踢出自己课程的所有学生
        elif request.user.role == 'TEACHER':
            return True
        # 管理员可以踢出任何学生
        if request.user.role == 'ADMIN':
            return True
        return False
    
class CanSelectSubject(permissions.BasePermission):
    """检查用户是否可以选题"""
    def has_object_permission(self, request, view, obj):
        # 学生组长可以选题
        if request.user.role == 'STUDENT':
            return obj.creator == request.user
        # 管理员可以选题
        if request.user.role == 'ADMIN':
            return True
        # 教师可以选题
        if request.user.role == 'TEACHER':
            return obj.course.teacher == request.user
        return False
    
class CanUnselectSubject(permissions.BasePermission):
    """检查用户是否可以退选课题"""
    def has_object_permission(self, request, view, obj):
        # 学生组长可以退选课题
        if request.user.role == 'STUDENT':
            return obj.creator == request.user
        # 管理员可以退选课题
        if request.user.role == 'ADMIN':
            return True
        # 教师可以退选课题
        if request.user.role == 'TEACHER':
            return obj.course.teacher == request.user
        return False
# endregion

# region 代码版本权限
class CanSubmitCode(permissions.BasePermission):
    """检查用户是否可以提交代码"""
    def has_permission(self, request, view):
        # 学生可以提交代码
        if request.user.role == 'STUDENT':
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        # 只有组长可以提交代码
        if request.user.role == 'STUDENT':
            return obj.creator == request.user
        return False
# endregion