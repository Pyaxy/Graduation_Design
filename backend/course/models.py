from django.db import models
from accounts.models import User
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError

# region 课程模型
class Course(models.Model):
    STATUS_CHOICES = (
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('completed', '已结束'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='课程名称')
    description = models.TextField(verbose_name='课程描述', blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_courses', verbose_name='教师')
    students = models.ManyToManyField(User, related_name='enrolled_courses', verbose_name='学生', blank=True)
    course_code = models.CharField(max_length=10, unique=True, verbose_name='课程码')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name='课程状态')
    max_group_size = models.PositiveIntegerField(verbose_name='最大小组人数', default=3)
    min_group_size = models.PositiveIntegerField(verbose_name='最小小组人数', default=1)
    max_subject_selections = models.PositiveIntegerField(verbose_name='最大课题选择数', default=3)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')

    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def calculate_status(self):
        """根据当前时间和课程的开始/结束日期计算状态"""
        today = timezone.now().date()
        if today < self.start_date:
            return 'not_started'
        elif today > self.end_date:
            return 'completed'
        else:
            return 'in_progress'

    def save(self, *args, **kwargs):
        """重写save方法，在保存时自动更新状态"""
        self.status = self.calculate_status()
        super().save(*args, **kwargs)
# endregion

# region 小组模型
class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='小组名称')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_groups', verbose_name='课程')
    students = models.ManyToManyField(User, related_name='user_groups', verbose_name='学生', blank=True)
    max_students = models.PositiveIntegerField(verbose_name='最大学生数', null=True)
    min_students = models.PositiveIntegerField(verbose_name='最小学生数', null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups', verbose_name='创建者', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '小组'
        verbose_name_plural = '小组'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.course.name})"
    
    def save(self, *args, **kwargs):
        """重写save方法，在保存时自动更新状态"""
        # 新建小组时
        # is_new = not self.pk
        is_new = self._state.adding
        if is_new:
            # 设置小组名字
            group_count = Group.objects.filter(course=self.course).count()
            self.name = f"{self.course.name} 小组 {group_count + 1}"

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """重写delete方法，在删除后自动更新小组名称"""
        # 获取小组对应的课程
        course = self.course
        # 删除小组
        super().delete(*args, **kwargs)
        groups= Group.objects.filter(course=course)
        for index, group in enumerate(groups, 1):
            group.name = f"{course.name} 小组 {index}"
            group.save(update_fields=['name'])
    
# endregion

# region 课程课题关联模型
class CourseSubject(models.Model):
    """课程课题关联模型"""
    SUBJECT_TYPE_CHOICES = (
        ('PRIVATE', '私有课题'),
        ('PUBLIC', '公开课题'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_subjects', verbose_name='课程')
    subject_type = models.CharField(max_length=10, choices=SUBJECT_TYPE_CHOICES, verbose_name='课题类型')
    private_subject = models.ForeignKey('subject.Subject', on_delete=models.CASCADE, related_name='course_subjects', verbose_name='私有课题', null=True, blank=True)
    public_subject = models.ForeignKey('subject.PublicSubject', on_delete=models.CASCADE, related_name='course_subjects', verbose_name='公开课题', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '课程课题'
        verbose_name_plural = '课程课题'
        ordering = ['-created_at']
        unique_together = [
            ('course', 'private_subject'),
            ('course', 'public_subject')
        ]
    
    def __str__(self):
        if self.subject_type == 'PRIVATE':
            return f"{self.course.name} - {self.private_subject.title}"
        else:
            return f"{self.course.name} - {self.public_subject.title}"
    
    def clean(self):
        """验证课题类型和课题ID的对应关系"""
        if self.subject_type == 'PRIVATE' and not self.private_subject:
            raise ValidationError("私有课题不能为空")
        if self.subject_type == 'PUBLIC' and not self.public_subject:
            raise ValidationError("公开课题不能为空")
        if self.subject_type == 'PRIVATE' and self.public_subject:
            raise ValidationError("私有课题不能关联公开课题")
        if self.subject_type == 'PUBLIC' and self.private_subject:
            raise ValidationError("公开课题不能关联私有课题")
    
    def save(self, *args, **kwargs):
        """重写save方法，在保存时进行验证"""
        self.clean()
        super().save(*args, **kwargs)
# endregion

# region 小组选题模型
class GroupSubject(models.Model):
    """小组选题模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_subjects', verbose_name='小组')
    course_subject = models.ForeignKey(CourseSubject, on_delete=models.CASCADE, related_name='group_subjects', verbose_name='课程课题')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '小组选题'
        verbose_name_plural = '小组选题'
        ordering = ['-created_at']
        unique_together = ['group', 'course_subject']
    
    def __str__(self):
        return f"{self.group.name} - {self.course_subject}"
    
    def clean(self):
        """验证选题是否合法"""
        pass
    
    def save(self, *args, **kwargs):
        """重写save方法，在保存时进行验证"""
        self.clean()
        super().save(*args, **kwargs)
# endregion

# region 代码版本模型
class GroupCodeVersion(models.Model):
    """小组代码版本模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='code_versions', verbose_name='小组')
    version = models.CharField(max_length=50, verbose_name='版本号')
    description = models.TextField(verbose_name='版本描述', blank=True)
    zip_file = models.FileField(upload_to='group_codes/zip/%Y/%m/%d/', verbose_name='ZIP文件')
    total_files = models.IntegerField(default=0, verbose_name='文件总数')
    total_size = models.BigIntegerField(default=0, verbose_name='总大小(字节)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '代码版本'
        verbose_name_plural = '代码版本'
        ordering = ['-created_at']
        unique_together = ['group', 'version']
    
    def __str__(self):
        return f"{self.group.name} - {self.version}"
    
# endregion

# region 代码文件模型
class GroupCodeFile(models.Model):
    """小组代码文件模型"""
    # 可预览的文件类型
    PREVIEWABLE_EXTENSIONS = [
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', '.less',
        '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.swift', '.kt',
        '.md', '.txt', '.json', '.xml', '.yml', '.yaml', '.ini', '.conf',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(GroupCodeVersion, on_delete=models.CASCADE, related_name='files', verbose_name='版本')
    path = models.CharField(max_length=500, verbose_name='文件路径')
    content = models.TextField(verbose_name='文件内容', null=True, blank=True)
    size = models.BigIntegerField(verbose_name='文件大小(字节)')
    is_previewable = models.BooleanField(default=False, verbose_name='是否可预览')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '代码文件'
        verbose_name_plural = '代码文件'
        ordering = ['path']
        unique_together = ['version', 'path']
    
    def __str__(self):
        return f"{self.version.group.name} - {self.path}"
    
    def save(self, *args, **kwargs):
        """重写save方法，在保存时判断文件是否可预览"""
        # 获取文件扩展名
        import os
        _, ext = os.path.splitext(self.path)
        # 判断文件是否可预览
        self.is_previewable = ext.lower() in self.PREVIEWABLE_EXTENSIONS
        super().save(*args, **kwargs)
# endregion

# region 小组提交模型
class GroupSubmission(models.Model):
    """小组提交模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='submissions', verbose_name='小组')
    code_version = models.ForeignKey(GroupCodeVersion, on_delete=models.CASCADE, related_name='submissions', verbose_name='代码版本')
    is_submitted = models.BooleanField(default=False, verbose_name='是否已提交')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '小组提交'
        verbose_name_plural = '小组提交'
        ordering = ['-created_at']
        unique_together = ['group', 'code_version']
    
    def __str__(self):
        return f"{self.group.name} - {self.code_version.version}"
    
    def save(self, *args, **kwargs):
        """重写save方法，在提交时自动设置提交时间"""
        if self.is_submitted and not self.submitted_at:
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)

class GroupSubmissionContribution(models.Model):
    """小组提交贡献度模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(GroupSubmission, on_delete=models.CASCADE, related_name='contributions', verbose_name='提交')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submission_contributions', verbose_name='学生')
    contribution = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='贡献度')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '提交贡献度'
        verbose_name_plural = '提交贡献度'
        ordering = ['-created_at']
        unique_together = ['submission', 'student']
    
    def __str__(self):
        return f"{self.student.name} - {self.contribution}%"
# endregion