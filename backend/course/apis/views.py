from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Course
from .serializers import CourseSerializer, JoinCourseSerializer
import random
import string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from accounts.permissions import IsStudent, IsTeacherOrAdmin, CanUpdateCourse, CanDeleteCourse
from CodeCollab.api.decorators import standard_response
from .serializers import CourseCreateSerializer
from rest_framework.exceptions import ValidationError
# Create your views here.

class CustomPagination(PageNumberPagination):
    """自定义分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CourseViewSet(viewsets.ModelViewSet):
    """课程视图集"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'course_code', 'teacher__name']
    search_param = 'search'  # 指定搜索参数名为 search
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    pagination_class = CustomPagination

    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        if self.action == 'create':
            permission_classes = [IsTeacherOrAdmin]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanUpdateCourse]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, CanDeleteCourse]
        elif self.action == 'join':
            permission_classes = [IsStudent]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
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
        
    def perform_create(self, serializer):
        # 生成唯一的课程码
        while True:
            course_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Course.objects.filter(course_code=course_code).exists():
                break
        
        serializer.save(teacher=self.request.user, course_code=course_code)

    @action(detail=False, methods=['post'])
    @standard_response("加入课程成功")
    def join(self, request):
        serializer = JoinCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_code = serializer.validated_data['course_code']
        
        course = get_object_or_404(Course, course_code=course_code)
        if request.user in course.students.all():
            raise ValidationError("您已经加入该课程")
        # 更新课程状态
        course.calculate_status()
        # 如果课程已结束，则无法加入
        if course.status == "completed":
            raise ValidationError("该课程已结束，无法加入")
        
        course.students.add(request.user)
        return Response(None, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    @standard_response("退出课程成功")
    def leave(self, request, pk=None):
        course = self.get_object()
        if request.user not in course.students.all():
            raise ValidationError("您未加入该课程")
        # 更新课程状态
        course.calculate_status()
        # 如果课程已结束，则无法退出
        if course.status == "completed":
            raise ValidationError("该课程已结束，无法退出")
        course.students.remove(request.user)
        return Response(None, status=status.HTTP_200_OK)
