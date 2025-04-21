import logging
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from accounts.permissions import IsTeacherOrAdmin, IsTeacher, IsAdmin, CanDeleteSubject, CanUpdateSubject, CanApplyPublicSubject, CanReviewPublicSubject
from subject.models import Subject, PublicSubject
from subject.api.serializers import (
    SubjectSerializer, SubjectCreateSerializer, SubjectReviewSerializer,
    SubjectPublicApplySerializer, SubjectPublicReviewSerializer, PublicSubjectSerializer
)
from CodeCollab.api.decorators import standard_response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from django.core.files.base import ContentFile
import os
from django_filters import FilterSet, CharFilter

logger = logging.getLogger(__name__)

# region 分页
class CustomPagination(PageNumberPagination):
    """自定义分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
# endregion

class SubjectFilter(FilterSet):
    languages = CharFilter(method='filter_languages', required=False)

    def filter_languages(self, queryset, name, value):
        if not value:
            return queryset
        languages = [lang.strip() for lang in value.split(',')]
        return queryset.filter(languages__contains=languages)

    class Meta:
        model = Subject
        fields = ['status', 'public_status', 'languages']

class PublicSubjectFilter(FilterSet):
    languages = CharFilter(method='filter_languages', required=False)

    def filter_languages(self, queryset, name, value):
        if not value:
            return queryset
        languages = [lang.strip() for lang in value.split(',')]
        return queryset.filter(languages__contains=languages)

    class Meta:
        model = PublicSubject
        fields = ['languages']

# region 课题视图集
class SubjectViewSet(viewsets.ModelViewSet):
    """课题视图集"""
    # region 配置
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubjectFilter
    search_fields = ['title', 'description']
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
            permission_classes = [IsAuthenticated, CanUpdateSubject]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, CanDeleteSubject]
        elif self.action == 'apply_public':
            permission_classes = [IsAuthenticated, CanApplyPublicSubject]
        elif self.action == 'review_public':
            permission_classes = [IsAuthenticated, CanReviewPublicSubject]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    # endregion

    # region 序列化器
    def get_serializer_class(self):
        """根据不同的操作返回不同的序列化器"""
        if self.action == 'create':
            return SubjectCreateSerializer
        elif self.action == 'review':
            return SubjectReviewSerializer
        elif self.action == 'apply_public':
            return SubjectPublicApplySerializer
        elif self.action == 'review_public':
            return SubjectPublicReviewSerializer
        return SubjectSerializer
    # endregion

    # region 查询集
    def get_queryset(self):
        """根据用户角色过滤课题"""
        queryset = Subject.objects.all()
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        elif user.role == 'STUDENT':
            return queryset.filter(Q(status='APPROVED') & Q(public_status='APPROVED'))
        elif user.role == 'TEACHER':
            return queryset.filter(Q(creator=user) | (Q(status='APPROVED') & Q(public_status='APPROVED')))
        elif user.role == 'ADMIN':
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
        instance = self.get_object()
        if request.user.role != 'ADMIN':
            # 非管理员只能更新课题的标题、描述、描述文件
            allowed_fields = ['title', 'description', 'description_file', 'languages']
            # 检查请求数据中是否只包含允许的字段
            for field in request.data.keys():
                if field not in allowed_fields:
                    raise serializers.ValidationError({f"{field}": "不允许更新字段"})

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        # 设置状态为 PENDING
        serializer.validated_data['status'] = 'PENDING'
        serializer.validated_data['public_status'] = 'NOT_APPLIED'
        serializer.validated_data['public_reviewer'] = None # 公开审核人
        serializer.validated_data['public_review_comments'] = None # 公开审核意见
        serializer.validated_data['reviewer'] = None # 审核人
        serializer.validated_data['review_comments'] = None # 审核意见
        serializer.validated_data['is_public'] = False # 是否公开
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @standard_response("更新成功")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @standard_response("删除成功")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    # endregion

    # region 审核
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
    # endregion

    # region 公开
    @action(detail=True, methods=['post'], url_path='apply-public')
    @standard_response("申请公开成功")
    def apply_public(self, request, pk=None):
        """申请公开课题"""
        subject = self.get_object()
            
        # 检查课题状态
        if subject.status != 'APPROVED':
            raise serializers.ValidationError("只有审核通过的课题才能申请公开")
        
        # 检查课题是否已公开
        if subject.is_public:
            raise serializers.ValidationError("课题已公开，不能重复申请")
            
        serializer = self.get_serializer(subject, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # 设置公开状态为待审核
        serializer.validated_data['public_status'] = 'PENDING'
        serializer.save()
        return serializer.data

    @action(detail=True, methods=['post'], url_path='review-public')
    @standard_response("公开审核操作成功")
    def review_public(self, request, pk=None):
        """审核公开申请"""
        subject = self.get_object()
        if subject.status != 'APPROVED':
            raise serializers.ValidationError("只有审核通过的课题才能进行公开审核")
        
        if subject.public_status == 'NOT_APPLIED':
            raise serializers.ValidationError("课题未申请公开，不能进行公开审核")
        
        # 检查课题是否已公开
        if subject.is_public:
            raise serializers.ValidationError("课题已公开，不能重复申请")
        
        
        serializer = self.get_serializer(subject, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        serializer.validated_data['is_public'] = True
        
        # 如果审核通过，创建公开版本
        if serializer.validated_data['public_status'] == 'APPROVED':
            # 获取最新的公开版本号
            latest_version = PublicSubject.objects.filter(original_subject=subject).order_by('-version').first()
            version = 1 if not latest_version else latest_version.version + 1
            
            # 创建公开版本
            public_subject = PublicSubject.objects.create(
                original_subject=subject,
                title=subject.title,
                description=subject.description,
                creator=subject.creator,
                languages=subject.languages,
                version=version
            )
            
            # 复制文件
            if subject.description_file:
                file_name = os.path.basename(subject.description_file.name)
                public_subject.description_file.save(
                    file_name,
                    ContentFile(subject.description_file.read())
                )
        
        serializer.save()
        return Response(serializer.data)
    # endregion
# endregion


# region 公开课题视图集
class PublicSubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """公开课题视图集"""
    queryset = PublicSubject.objects.all()
    serializer_class = PublicSubjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PublicSubjectFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """所有用户都可以查看公开的课题"""
        return PublicSubject.objects.all()
    
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
    
# endregion