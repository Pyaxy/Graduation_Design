from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Course, Group
from .serializers import CourseSerializer, JoinCourseSerializer, LeaveCourseSerializer, UserSerializer
import random
import string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from accounts.permissions import IsStudent, IsTeacherOrAdmin, CanUpdateCourse, CanDeleteCourse, CanLeaveCourse, CanSeeStudents
from CodeCollab.api.decorators import standard_response
from .serializers import CourseCreateSerializer, GroupSerializer, GroupCreateSerializer
from rest_framework.exceptions import ValidationError
from accounts.models import User
from django.http import Http404
from django.db.models import Q
# Create your views here.

class CustomPagination(PageNumberPagination):
    """自定义分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# region 课程视图集
class CourseViewSet(viewsets.ModelViewSet):
    """课程视图集"""
    # region 配置
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'course_code', 'teacher__name', 'students__name']
    search_param = 'search'  # 指定搜索参数名为 search
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    pagination_class = CustomPagination
    # endregion

    # region 权限
    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        if self.action == 'create':
            permission_classes = [IsTeacherOrAdmin]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanUpdateCourse]
        elif self.action == 'destroy':
            permission_classes = [IsTeacherOrAdmin, CanDeleteCourse]
        elif self.action in ['join']:
            permission_classes = [IsStudent]
        elif self.action in ['leave']:
            permission_classes = [IsAuthenticated, CanLeaveCourse]
        elif self.action in ['students']:
            permission_classes = [IsAuthenticated, CanSeeStudents]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    # endregion

    # region 序列化器
    def get_serializer_class(self):
        """根据不同的操作设置不同的序列化器"""
        if self.action == 'create':
            return CourseCreateSerializer
        return super().get_serializer_class()
    # endregion

    # region 查询集
    def get_queryset(self):
        """根据不同的操作设置不同的查询集"""
        user = self.request.user
        queryset = Course.objects.all()

        # 根据用户角色过滤数据
        if user.is_anonymous:
            return queryset.none()
        elif user.role == 'STUDENT':
            # 学生只能看到自己加入的课程
            return queryset.filter(students=user)
        elif user.role == 'TEACHER':
            # 教师可以看到自己创建的课程
            return queryset.filter(teacher=user)
        elif user.role == 'ADMIN':
            # 管理员可以看到所有课程
            return queryset
        return queryset.none()
    # endregion

    # region CRUD
    @standard_response("获取列表成功")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @standard_response("获取详情成功")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @standard_response("创建成功")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @standard_response("更新成功")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @standard_response("更新成功")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @standard_response("删除成功")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    # endregion
    def perform_create(self, serializer):
        # 生成唯一的课程码
        while True:
            course_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Course.objects.filter(course_code=course_code).exists():
                break
        
        serializer.save(teacher=self.request.user, course_code=course_code)

    # region 加入课程
    @action(detail=False, methods=['post'])
    @standard_response("加入课程成功")
    def join(self, request):
        # 验证请求参数
        serializer = JoinCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_code = serializer.validated_data['course_code']
        # 获取课程
        course = get_object_or_404(Course, course_code=course_code)
        # 验证用户是否已经加入课程
        if request.user in course.students.all():
            raise ValidationError("您已经加入该课程")
        # 更新课程状态
        course.calculate_status()
        # 如果课程已结束，则无法加入
        if course.status == "completed":
            raise ValidationError("该课程已结束，无法加入")
        # 加入课程
        course.students.add(request.user)
        # 保存课程
        course.save()
        return Response(None, status=status.HTTP_200_OK)
    # endregion

    # region 退出课程
    @action(detail=True, methods=['post'])
    @standard_response("退出课程成功")
    def leave(self, request, pk=None):
        try:
            # 获取课程
            course = self.get_object()
        except Http404:
            raise Http404("课程不存在")
            
        # 如果是学生退出自己的课程
        if request.user.role == "STUDENT":
            # 更新课程状态
            course.calculate_status()
            # 如果课程已结束，则无法退出
            if course.status == "completed":
                raise ValidationError("该课程已结束，无法退出")
            # 退出课程
            course.students.remove(request.user)
            # 保存课程
            course.save()
        else:
            # 验证请求参数
            serializer = LeaveCourseSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            student_user_id = serializer.validated_data['student_user_id']
            student_user = get_object_or_404(User, user_id=student_user_id)
            # 验证用户是否已经加入课程
            if student_user not in course.students.all():
                raise ValidationError("该学生未加入该课程")
            # 退出课程
            course.students.remove(student_user)
            # 保存课程
            course.save()
        return Response(None, status=status.HTTP_200_OK)
    # endregion

    # region 获取学生列表
    @action(detail=True, methods=['get'])
    @standard_response("获取学生列表成功")
    def students(self, request, *args, **kwargs):
        course = self.get_object()
        students = course.students.all()

        # 搜索, 搜索学生姓名或学号
        search = request.query_params.get('student_search', '')
        if search:
            students = students.filter(Q(name__icontains=search) | Q(user_id__icontains=search))

        # 分页
        page = self.paginate_queryset(students)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)
    # endregion

# endregion



# region 小组视图集
class GroupViewSet(viewsets.ModelViewSet):
    """小组视图集"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    # region 权限
    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        # 创建小组需要学生权限
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    # endregion

    # region 序列化器
    def get_serializer_class(self):
        """根据不同的操作设置不同的序列化器"""
        if self.action == 'create':
            return GroupCreateSerializer
        return GroupSerializer
    # endregion
    
    # region CRUD
    @standard_response("创建成功")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.validated_data['course']
        # 验证用户是否是课程学生
        user = request.user
        if user.role == 'STUDENT' and user not in course.students.all():
            raise Http404("未查询到该课程")
        if user.role == "TEACHER" and user != course.teacher:
            raise Http404("未查询到该课程")
        self.perform_create(serializer)
        return Response(None, status=status.HTTP_201_CREATED)
    # endregion
    
# endregion
