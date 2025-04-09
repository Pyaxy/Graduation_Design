import logging
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from accounts.permissions import IsTeacherOrAdmin, IsTeacher, IsAdmin, CanDeleteSubject, CanUpdateSubject
from subject.models import Subject
from subject.api.serializers import (
    SubjectSerializer, SubjectCreateSerializer, SubjectReviewSerializer
)
from CodeCollab.api.decorators import standard_response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
# from CodeCollab.api.exceptions import standardize_exceptions

logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    """自定义分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SubjectViewSet(viewsets.ModelViewSet):
    """课题视图集"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    search_param = 'search'  # 指定搜索参数名为 search
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    pagination_class = CustomPagination

    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        if self.action == 'create':
            permission_classes = [IsTeacherOrAdmin]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanUpdateSubject]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, CanDeleteSubject]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """根据不同的操作返回不同的序列化器"""
        if self.action == 'create':
            return SubjectCreateSerializer
        elif self.action == 'review':
            return SubjectReviewSerializer
        return SubjectSerializer

    def get_queryset(self):
        """根据用户角色过滤课题"""
        user = self.request.user
        queryset = Subject.objects.all()
        
        # 根据用户角色过滤数据
        if user.is_anonymous:
            return queryset.none()
        elif user.role == 'STUDENT':
            # 学生只能看到已审核通过的课题
            return queryset.filter(status='APPROVED')
        elif user.role == 'TEACHER':
            # 教师可以看到自己创建的课题和已审核通过的课题
            return queryset.filter(Q(creator=user) | Q(status='APPROVED'))
        elif user.role == 'ADMIN':
            # 管理员可以看到所有课题
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
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        # 设置状态为 PENDING
        serializer.validated_data['status'] = 'PENDING'
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @standard_response("更新成功")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @standard_response("删除成功")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='review')
    @standard_response("审核操作成功")
    def review(self, request, pk=None):
        """审核课题"""
        subject = self.get_object()
        
        # 检查权限
        if request.user.role != 'ADMIN':
            return Response({"message": "只有管理员可以审核课题"}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(subject, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data