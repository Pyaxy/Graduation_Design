from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Course, Group, GroupCodeVersion, GroupCodeFile, GroupSubmission, GroupSubmissionContribution
from .serializers import CourseSerializer, JoinCourseSerializer, LeaveCourseSerializer, UserSerializer, GroupCodeVersionSerializer, GroupCodeVersionCreateSerializer, GroupCodeVersionListSerializer
import random
import string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from accounts.permissions import IsStudent, IsTeacherOrAdmin, CanUpdateCourse, CanDeleteCourse, CanLeaveCourse, CanSeeStudents, CanJoinGroup, CanLeaveGroup, CanAddSubjectToCourse, CanSeeSubjects, CanDeleteSubjectFromCourse, CanSelectSubject, CanUnselectSubject, CanSeeGroupDetail, CanSubmitCode
from CodeCollab.api.decorators import standard_response
from .serializers import CourseCreateSerializer, GroupSerializer, GroupCreateSerializer, LeaveGroupSerializer, AddSubjectSerializer, CourseSubjectSerializer, DeleteSubjectSerializer, SelectSubjectSerializer, GroupSubmissionCreateSerializer
from rest_framework.exceptions import ValidationError
from accounts.models import User
from django.http import Http404
from django.db.models import Q
import logging
from subject.models import Subject, PublicSubject
from course.models import CourseSubject, GroupSubject
import os
from io import BytesIO
from django.http import FileResponse

logger = logging.getLogger(__name__)
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
        elif self.action in ['add_subject']:
            permission_classes = [IsAuthenticated, CanAddSubjectToCourse]
        elif self.action in ['subjects_list']:
            permission_classes = [IsAuthenticated, CanSeeSubjects]
        elif self.action in ['delete_subject']:
            permission_classes = [IsAuthenticated, CanDeleteSubjectFromCourse]
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
        if course.status == "in_progress":
            raise ValidationError("该课程正在进行中，无法加入")
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
            # 如果课程进行中，则无法退出
            if course.status == "in_progress":
                raise ValidationError("该课程正在进行中，无法退出")
            # 退出课程
            course.students.remove(request.user)
            # 同步退出所有相关小组
            groups = Group.objects.filter(course=course, students=request.user)
            if groups.exists():
                for group in groups:
                    # 如果是组长退出课程
                    if group.creator == request.user:
                        group.students.remove(request.user)
                        # 如果小组没有学生了，则删除小组，否则重新指定组长
                        if group.students.count() == 0:
                            group.delete()
                        else:
                            group.creator = group.students.first()
                            group.save()
                    else:
                        group.students.remove(request.user)
                        group.save()
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
            # 同步退出所有相关小组
            groups = Group.objects.filter(course=course, students=student_user)
            for group in groups:
                group.students.remove(student_user)
                # 如果小组没有学生了，且不是教师创建的小组，则删除小组
                if group.students.count() == 0 and group.creator != course.teacher:
                    group.delete()
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

    # region 添加课题
    @action(detail=True, methods=['post'])
    @standard_response("请求成功")
    def add_subject(self, request, pk=None):
        """批量添加课题到课程"""
        """相应格式:
        {
            "success": {
                "count": 1,
                "ids": [1, 2, 3]
            },
            "failed": {
                "count": 1,
                "details": [
                    {
                        "id": 1,
                        "reason": "您没有权限添加此课题"
                    }
                ]
            }
        }
        """
        # 获取课程
        try:
            course = self.get_object()
        except Http404:
            raise Http404("未查询到该课程")
        
        # 验证请求参数
        serializer = AddSubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        subject_ids = serializer.validated_data['subject_ids']
        subject_type = serializer.validated_data['subject_type']

        # 状态验证
        if course.status == "in_progress":
            raise ValidationError("课程正在进行中，无法添加课题")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法添加课题")
        
        # 用于存储成功添加的课题ID
        success_ids = []
        # 用于存储失败的课题ID和原因
        failed_ids = []
        
        # 根据课题类型处理课题
        if subject_type == 'PRIVATE':
            for subject_id in subject_ids:
                try:
                    subject = Subject.objects.get(id=subject_id)
                    # 只能添加审核通过的课题
                    if subject.status != 'APPROVED':
                        failed_ids.append({
                            'id': subject_id,
                            'reason': "课题未审核通过"
                        })
                        continue
                    # 只有课题的创建者或者管理员才能添加课题
                    if subject.creator != request.user and request.user.role != 'ADMIN':
                        failed_ids.append({
                            'id': subject_id,
                            'reason': "您没有权限添加此课题"
                        })
                        continue
                    
                    # 检查是否已经添加过该课题
                    if CourseSubject.objects.filter(course=course, private_subject=subject).exists():
                        failed_ids.append({
                            'id': subject_id,
                            'reason': "该课题已经添加到课程中"
                        })
                        continue
                    
                    # 创建课程课题关联
                    CourseSubject.objects.create(
                        course=course,
                        subject_type='PRIVATE',
                        private_subject=subject
                    )
                    success_ids.append(subject_id)
                    
                except Subject.DoesNotExist:
                    failed_ids.append({
                        'id': subject_id,
                        'reason': "课题不存在"
                    })
            
        else:  # PUBLIC
            for subject_id in subject_ids:
                try:
                    subject = PublicSubject.objects.get(id=subject_id)
                    
                    # 检查是否已经添加过该课题
                    if CourseSubject.objects.filter(course=course, public_subject=subject).exists():
                        failed_ids.append({
                            'id': subject_id,
                            'reason': "该课题已经添加到课程中"
                        })
                        continue
                    
                    # 创建课程课题关联
                    CourseSubject.objects.create(
                        course=course,
                        subject_type='PUBLIC',
                        public_subject=subject
                    )
                    success_ids.append(subject_id)
                    
                except PublicSubject.DoesNotExist:
                    failed_ids.append({
                        'id': subject_id,
                        'reason': "公开课题不存在"
                    })
        
        # 构建返回数据
        response_data = {
            'success': {
                'count': len(success_ids),
                'ids': success_ids
            },
            'failed': {
                'count': len(failed_ids),
                'details': failed_ids
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    # endregion

    # region 获取课程课题列表
    @action(detail=True, methods=['get'])
    @standard_response("获取课程课题列表成功")
    def subjects_list(self, request, pk=None):
        """获取课程的所有课题"""
        course = self.get_object()
        course_subjects = CourseSubject.objects.filter(course=course)
        
        # 分页
        page = self.paginate_queryset(course_subjects)
        if page is not None:
            serializer = CourseSubjectSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        # 如果没有分页，返回所有数据
        serializer = CourseSubjectSerializer(course_subjects, many=True, context={'request': request})
        return Response(serializer.data)
    # endregion

    # region 删除课程课题
    @action(detail=True, methods=['delete'])
    @standard_response("删除课程课题成功")
    def delete_subject(self, request, pk=None):
        """删除课程课题"""
        try:
            course = self.get_object()
        except Http404:
            raise Http404("未查询到该课程")
        if course.status == "in_progress":
            raise ValidationError("课程正在进行中，无法删除课题")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法删除课题")
        # 验证请求参数
        serializer = DeleteSubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_subject_id = serializer.validated_data['course_subject_id']
        
        try:
            course_subject = CourseSubject.objects.get(course=course, id=course_subject_id)
            course_subject.delete()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except CourseSubject.DoesNotExist:
            raise Http404("未查询到该课程课题")
    # endregion

    # region 下载提交
    @action(detail=True, methods=['get'])
    def download_submissions(self, request, pk=None):
        """下载所有小组的提交信息"""
        try:
            course = self.get_object()
        except Http404:
            raise Http404("课程不存在")
        
        # 验证课程状态
        if course.status != 'completed':
            raise ValidationError("课程未结束，无法下载提交信息")
        
        # 获取所有小组
        groups = Group.objects.filter(course=course)
        
        # 创建内存缓冲区
        buffer = BytesIO()
        
        try:
            # 创建ZIP文件
            import zipfile
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 创建CSV内容
                import csv
                from io import StringIO
                csv_buffer = StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(['小组名称', '课题名称', '成员贡献'])
                
                # 遍历所有小组
                for group in groups:
                    try:
                        submission = GroupSubmission.objects.get(group=group)
                        group_subject = GroupSubject.objects.get(group=group)
                        
                        # 获取课题名称
                        if group_subject.course_subject.subject_type == 'PRIVATE':
                            subject_title = group_subject.course_subject.private_subject.title
                        else:
                            subject_title = group_subject.course_subject.public_subject.title
                        
                        # 获取成员贡献
                        contributions = GroupSubmissionContribution.objects.filter(submission=submission)
                        contribution_str = ', '.join([f"{c.student.name}({c.contribution}%)" for c in contributions])
                        
                        # 写入CSV
                        writer.writerow([
                            group.name,
                            subject_title,
                            contribution_str
                        ])
                        
                        # 添加代码文件到ZIP
                        code_version = submission.code_version
                        if code_version.zip_file:
                            from django.core.files.storage import default_storage
                            with default_storage.open(code_version.zip_file.name) as f:
                                zipf.writestr(
                                    f"code/{group.name}/{group.name}.zip",
                                    f.read()
                                )
                    except (GroupSubmission.DoesNotExist, GroupSubject.DoesNotExist):
                        # 如果小组未提交或未选题，写入默认值
                        writer.writerow([
                            group.name,
                            '未选题',
                            '未提交(-1)'
                        ])
                
                # 将CSV内容添加到ZIP
                zipf.writestr('submissions.csv', csv_buffer.getvalue())
        except Exception as e:
            buffer.close()
            raise e
        
        # 重置缓冲区位置
        buffer.seek(0)
        
        # 创建支持关闭回调的FileResponse子类
        class CleanupFileResponse(FileResponse):
            def __init__(self, *args, buffer, **kwargs):
                super().__init__(*args, **kwargs)
                self.buffer = buffer
            
            def close(self):
                super().close()
                if not self.buffer.closed:
                    self.buffer.close()

        response = CleanupFileResponse(
            buffer,
            as_attachment=True,
            filename=f"submissions_{course.name}.zip",
            content_type='application/zip',
            buffer=buffer  # 传递buffer引用
        )
        response['Content-Length'] = buffer.getbuffer().nbytes
        
        return response
    # endregion

# endregion

# region 小组视图集
class GroupViewSet(viewsets.ModelViewSet):
    """小组视图集"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = CustomPagination

    # region 权限
    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        # 创建小组需要学生权限
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            permission_classes = [IsAuthenticated, CanSeeGroupDetail]
        elif self.action == 'join':
            permission_classes = [IsAuthenticated, CanJoinGroup]
        elif self.action == 'leave':
            permission_classes = [IsAuthenticated, CanLeaveGroup]
        elif self.action == 'select_subject':
            permission_classes = [IsAuthenticated, CanSelectSubject]
        elif self.action == 'unselect_subject':
            permission_classes = [IsAuthenticated, CanUnselectSubject]
        elif self.action == 'submit_code':
            permission_classes = [IsAuthenticated, CanSubmitCode]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    # endregion

    # region 序列化器
    def get_serializer_class(self):
        """根据不同的操作设置不同的序列化器"""
        if self.action == 'create':
            return GroupCreateSerializer
        elif self.action == 'leave':
            return LeaveGroupSerializer
        elif self.action == 'submit_code':
            return GroupSubmissionCreateSerializer
        return GroupSerializer
    # endregion

    # region 查询集
    def get_queryset(self):
        """根据不同的操作设置不同的查询集"""
        user = self.request.user
        queryset = Group.objects.all()
        # 教师查询集
        if user.role == "TEACHER":
            return queryset.filter(course__teacher=user)
        # 学生查询集
        elif user.role == "STUDENT":
            return queryset.filter(course__students=user)
        return queryset
    # endregion
    
    # region CRUD
    @standard_response("创建成功")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.validated_data['course']
        user = request.user
        groups = Group.objects.filter(course=course)
        # 学生权限
        if user.role == 'STUDENT':
            # 学生必须在课程中
            if user not in course.students.all():
                raise Http404("未查询到该课程")
            # 如果已经加入了小组，则无法创建小组
            if groups.filter(students=user).exists():
                raise ValidationError("您已经加入了小组")
        # 教师权限
        if user.role == "TEACHER" or user.role == "ADMIN":
            # 教师必须在课程中
            if user != course.teacher:
                raise Http404("未查询到该课程")
        # 课程必须未开始
        if course.status == "in_progress":
            raise ValidationError("课程已开始")
        # 如果课程已结束，则无法创建小组
        if course.status == "completed":
            raise ValidationError("课程已结束")
        self.perform_create(serializer)
        return Response(None, status=status.HTTP_201_CREATED)
    
    @standard_response("获取列表成功")
    def list(self, request, *args, **kwargs):
        # 从查询参数中获取course_id
        course_id = request.query_params.get('course_id')
        if not course_id:
            raise ValidationError("请提供课程ID")
        
        # 验证课程是否存在
        course = get_object_or_404(Course, id=course_id)
        
        # 权限判断
        user = request.user
        if user.role == "STUDENT":
            # 学生只能查看自己加入的课程的小组列表
            if user not in course.students.all():
                raise Http404("未查询到该课程")
        elif user.role == "TEACHER":
            # 教师只能查看自己教授的课程的小组列表
            if user != course.teacher:
                raise Http404("未查询到该课程")
        elif user.role == "ADMIN":
            # 管理员可以查看所有课程的小组列表
            pass
        else:
            raise Http404("未查询到该课程")
        
        # 过滤查询集
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(course=course)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @standard_response("更新成功")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @standard_response("删除成功")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @standard_response("获取详情成功")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    # endregion
    
    # region 加入小组
    @action(detail=True, methods=['post'])
    @standard_response("加入小组成功")
    def join(self, request, *args, **kwargs):
        try:
            group = self.get_object()
        except Http404:
            raise Http404("未查询到该小组")
        course = group.course
        user = request.user

        # 验证用户是否已加入课程
        if user not in course.students.all():
            raise ValidationError("您未加入该课程，无法加入小组")

        # 验证课程状态
        if course.status == "in_progress":
            raise ValidationError("课程已开始，无法加入小组")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法加入小组")

        # 验证小组是否已满
        if group.students.count() >= course.max_group_size:
            raise ValidationError("小组人数已满，无法加入")

        # 验证用户是否已加入该小组
        if user in group.students.all():
            raise ValidationError("您已经加入该小组")

        # 验证用户是否已加入其他小组
        if Group.objects.filter(course=course, students=user).exists():
            raise ValidationError("您已经加入了其他小组，无法重复加入")

        # 加入小组
        group.students.add(user)
        group.save()

        return Response(None, status=status.HTTP_200_OK)
    # endregion

    # region 退出小组
    @action(detail=True, methods=['post'])
    @standard_response("退出小组成功")
    def leave(self, request, *args, **kwargs):
        try:
            # 获取小组
            group = self.get_object()
        except Http404:
            raise Http404("未查询到该小组")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_user_id = serializer.validated_data['student_user_id']

        # 获取操作用户
        payload_user = User.objects.get(user_id=student_user_id)
        # 获取请求用户
        request_user = request.user
        # 获取课程
        course = group.course

        # 验证课程状态
        if course.status == "in_progress":
            raise ValidationError("课程已开始，无法退出小组")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法退出小组")
        
        # 学生发出请求
        if request_user.role == "STUDENT":
            # 学生自己申请退出, 此时经过权限验证，request_user一定在group中
            if payload_user.user_id == request_user.user_id:
                # 如果是组长，则需要重新指定组长
                if group.creator == payload_user:
                    group.students.remove(payload_user)
                    # 如果小组没有学生了，则删除小组，否则重新指定组长
                    if group.students.count() == 0:
                        group.delete()
                        return Response(None, status=status.HTTP_200_OK)
                    else:
                        group.creator = group.students.first()
                        group.save()
                else:
                    group.students.remove(payload_user)
                    group.save()
            # 学生组长踢出学生
            else:
                if request_user != group.creator:
                    raise ValidationError("您不是组长，无法踢出学生")
                if request_user not in course.students.all():
                    raise ValidationError("您未加入该课程，无法踢出学生")
                if payload_user not in course.students.all():
                    raise ValidationError("该学生未加入该课程")
                if payload_user not in group.students.all():
                    raise ValidationError("该学生未加入该小组")
                group.students.remove(payload_user)
                group.save()
        # 教师发出请求
        elif request_user.role == "TEACHER" or request_user.role == "ADMIN":
            if payload_user not in course.students.all():
                raise ValidationError("该学生未加入该课程")
            if payload_user not in group.students.all():
                raise ValidationError("该学生未加入该小组")
            # 如果是组长，则需要重新指定组长
            if payload_user == group.creator:
                group.students.remove(payload_user)
                # 如果小组没有学生了，则删除小组，否则重新指定组长
                if group.students.count() == 0:
                    group.delete()
                    return Response(None, status=status.HTTP_200_OK)
                else:
                    group.creator = group.students.first()
                    group.save()
            else:
                group.students.remove(payload_user)
                group.save()
            group.save()
        return Response(None, status=status.HTTP_200_OK)
    # endregion

    # region 小组选题
    @action(detail=True, methods=['post'])
    @standard_response("小组选题成功")
    def select_subject(self, request, *args, **kwargs):
        """小组选题"""
        try:
            # 获取小组
            group = self.get_object()
        except Http404:
            raise Http404("未查询到该小组")
        
        # 验证请求参数
        serializer = SelectSubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_subject_id = serializer.validated_data['course_subject_id']
        
        try:
            # 获取课程课题
            course_subject = CourseSubject.objects.get(id=course_subject_id)
        except CourseSubject.DoesNotExist:
            raise Http404("未查询到该课程课题")
        
        # 验证小组是否属于该课程
        if group.course != course_subject.course:
            raise ValidationError("小组和课题不属于同一个课程")
        # 验证课程状态
        course = group.course
        if course.status == "in_progress":
            raise ValidationError("课程正在进行中，无法选题")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法选题")
        
        # 验证小组是否已经选择了课题
        if GroupSubject.objects.filter(group=group).exists():
            raise ValidationError("小组已经选择了课题")
        
        # 验证课题是否已被选择超过最大次数
        current_selections = GroupSubject.objects.filter(course_subject=course_subject).count()
        if current_selections >= course.max_subject_selections:
            raise ValidationError(f"该课题已被选择超过最大次数（{course.max_subject_selections}次）")
        
        # 创建小组选题
        try:
            GroupSubject.objects.create(
                group=group,
                course_subject=course_subject
            )
        except ValidationError as e:
            raise ValidationError(str(e))
        
        return Response(None, status=status.HTTP_201_CREATED)
    # endregion

    # region 退选课题
    @action(detail=True, methods=['delete'])
    @standard_response("退选课题成功")
    def unselect_subject(self, request, *args, **kwargs):
        """退选课题"""
        try:
            # 获取小组
            group = self.get_object()
        except Http404:
            raise Http404("未查询到该小组")
        
        # 状态检查
        course = group.course
        if course.status == "in_progress":
            raise ValidationError("课程正在进行中，无法退选课题")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法退选课题")
        
        # 验证小组是否已经选择了课题
        if not GroupSubject.objects.filter(group=group).exists():
            raise ValidationError("小组未选择课题")
        
        # 删除小组选题
        GroupSubject.objects.filter(group=group).delete()
        
        return Response(None, status=status.HTTP_204_NO_CONTENT)
    # endregion

    # region 提交代码
    @action(detail=True, methods=['post'])
    @standard_response("提交代码成功")
    def submit_code(self, request, *args, **kwargs):
        """提交代码版本"""
        try:
            # 获取小组
            group = self.get_object()
        except Http404:
            raise Http404("小组不存在")
        
        # 验证课程状态
        course = group.course
        if course.status != "in_progress":
            raise ValidationError("课程未在进行中，无法提交代码")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法提交代码")
        
        # 验证小组是否选择了课题
        if not GroupSubject.objects.filter(group=group).exists():
            raise ValidationError("小组未选择课题，无法提交代码")
        
        # 验证用户是否在小组中
        if request.user not in group.students.all():
            raise ValidationError("您不在该小组中，无法提交代码")
        
        # 验证小组是否已经提交过代码
        if GroupSubmission.objects.filter(group=group).exists():
            raise ValidationError("小组已经提交过代码")
        
        # 创建提交记录
        serializer = self.get_serializer(data=request.data, context={'group': group})
        serializer.is_valid(raise_exception=True)
        serializer.save(group=group)
        
        return Response(None, status=status.HTTP_201_CREATED)
    # endregion

# endregion

# region 代码视图集
class GroupCodeVersionViewSet(viewsets.ModelViewSet):
    """代码版本视图集"""
    queryset = GroupCodeVersion.objects.all()
    serializer_class = GroupCodeVersionSerializer
    pagination_class = CustomPagination
    
    # region 代码视图集配置
    def get_queryset(self):
        """根据小组ID过滤版本"""
        user = self.request.user
        group_id = self.kwargs.get('group_pk')
        if user.role == "STUDENT":
            # 学生只能查看自己加入的小组
            return GroupCodeVersion.objects.filter(group_id=group_id, group__students=user)
        elif user.role == "TEACHER":
            # 教师可以查看自己教授的课程的小组
            return GroupCodeVersion.objects.filter(group_id=group_id, group__course__teacher=user)
        elif user.role == "ADMIN":
            # 管理员可以查看所有小组
            return GroupCodeVersion.objects.filter(group_id=group_id)
        else:
            raise Http404("未查询到该小组")
        
    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsStudent]
        elif self.action == 'list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """根据不同的操作设置不同的序列化器"""
        if self.action == 'create':
            return GroupCodeVersionCreateSerializer
        elif self.action == 'list':
            return GroupCodeVersionListSerializer
        return GroupCodeVersionSerializer
    
    def get_serializer_context(self):
        """添加小组到序列化器上下文"""
        context = super().get_serializer_context()
        user = self.request.user
        group_id = self.kwargs.get('group_pk')
        if user.role == "STUDENT":
            # 学生只能查看自己加入的小组
            context['group'] = get_object_or_404(Group, id=group_id, students=user)
        elif user.role == "TEACHER":
            # 教师可以查看自己教授的课程的小组
            context['group'] = get_object_or_404(Group, id=group_id, course__teacher=user)
        elif user.role == "ADMIN":
            context['group'] = get_object_or_404(Group, id=group_id)
        return context
    # endregion
    
    # region CRUD
    @standard_response("创建版本成功")
    def create(self, request, *args, **kwargs):
        """创建新版本"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 获取课程
        course = self.get_serializer_context()['group'].course
        # 获取小组
        group = self.get_serializer_context()['group']

        # 验证课程状态
        if course.status == "not_started":
            raise ValidationError("课程未开始，无法上传代码")
        if course.status == "completed":
            raise ValidationError("课程已结束，无法上传代码")
        
        # 验证小组是否选择了课题
        if not GroupSubject.objects.filter(group=group).exists():
            raise ValidationError("小组未选择课题，无法上传代码")
        
        # 验证小组是否已经提交过代码
        if GroupSubmission.objects.filter(group=group).exists():
            raise ValidationError("小组已经提交过代码，无法上传代码")
        
        # 创建版本
        version = serializer.save(group_id=group.id)
        
        try:
            # 解压ZIP文件
            import zipfile
            import os
            from django.conf import settings
            
            # 创建临时目录
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp', str(version.id))
            os.makedirs(temp_dir, exist_ok=True)
            
            # 解压文件
            with zipfile.ZipFile(version.zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 处理文件
            total_files = 0
            total_size = 0
            
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, temp_dir)
                    
                    # 跳过Mac系统特有的隐藏文件
                    if '__MACOSX' in relative_path or relative_path.startswith('._') or '.DS_Store' in relative_path:
                        continue
                    
                    # 获取文件大小
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    # 创建文件记录
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        content = None
                    
                    GroupCodeFile.objects.create(
                        version=version,
                        path=relative_path,
                        content=content,
                        size=file_size
                    )
                    total_files += 1
            
            # 更新版本信息
            version.total_files = total_files
            version.total_size = total_size
            version.save()
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir)
            
            return Response(GroupCodeVersionSerializer(version).data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # 如果处理失败，删除版本
            version.delete()
            raise ValidationError(f"处理ZIP文件失败: {str(e)}")
    
    @standard_response("获取版本列表成功")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @standard_response("获取版本详情成功")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @standard_response("删除版本成功")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    # endregion
# endregion
