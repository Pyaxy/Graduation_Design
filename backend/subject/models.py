from django.db import models
from django.contrib.postgres.fields import ArrayField
from accounts.models import User
from .validators import validate_pdf_file, validate_file_size

# Create your models here.

class Subject(models.Model):
    """
    课题模型：程序设计课程中的课题
    由老师创建，需要管理员审核，学生可以选择
    """
    STATUS_CHOICES = (
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已拒绝'),
    )

    PUBLIC_STATUS_CHOICES = (
        ('NOT_APPLIED', '未申请'),
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已拒绝'),
    )

    LANGUAGE_CHOICES = (
        ('C', 'C'),
        ('CPP', 'C++'),
        ('JAVA', 'Java'),
        ('PYTHON', 'Python'),
    )

    title = models.CharField(max_length=100, verbose_name="课题标题")
    description = models.TextField(verbose_name="课题描述")
    description_file = models.FileField(
        upload_to='subject_files/', 
        verbose_name="课题原始描述文件", 
        blank=True, 
        null=True,
        validators=[validate_pdf_file, validate_file_size]
    )
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="created_subjects",
        verbose_name="创建者",
        limit_choices_to={'role__in': ['TEACHER', 'ADMIN']}
    )
    languages = ArrayField(
        models.CharField(max_length=10, choices=LANGUAGE_CHOICES),
        verbose_name="适用语言",
        help_text="可多选",
        default=list
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="审核状态"
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="reviewed_subjects",
        verbose_name="审核人",
        limit_choices_to={'role': 'ADMIN'},
        null=True,
        blank=True
    )
    review_comments = models.TextField(verbose_name="审核意见", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    # 新增字段
    is_public = models.BooleanField(default=False, verbose_name="是否申请公开")
    public_status = models.CharField(
        max_length=20,
        choices=PUBLIC_STATUS_CHOICES,
        default='NOT_APPLIED',
        verbose_name="公开状态"
    )
    public_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="public_reviewed_subjects",
        verbose_name="公开审核人",
        limit_choices_to={'role': 'ADMIN'},
        null=True,
        blank=True
    )
    public_review_comments = models.TextField(verbose_name="公开审核意见", blank=True, null=True)

    class Meta:
        verbose_name = "课题"
        verbose_name_plural = "课题"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """删除对象时同时删除关联的文件"""
        if self.description_file:
            # 删除文件
            self.description_file.delete(save=False)
        # 调用父类的delete方法
        super().delete(*args, **kwargs)


class PublicSubject(models.Model):
    """
    公开课题模型：存储已公开的课题版本
    """
    original_subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="public_versions",
        verbose_name="原始课题"
    )
    title = models.CharField(max_length=100, verbose_name="课题标题")
    description = models.TextField(verbose_name="课题描述")
    description_file = models.FileField(
        upload_to='public_subject_files/', 
        verbose_name="课题原始描述文件", 
        blank=True, 
        null=True,
        validators=[validate_pdf_file, validate_file_size]
    )
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="public_created_subjects",
        verbose_name="创建者"
    )
    languages = ArrayField(
        models.CharField(max_length=10, choices=Subject.LANGUAGE_CHOICES),
        verbose_name="适用语言",
        help_text="可多选",
        default=list
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="公开时间")
    version = models.PositiveIntegerField(default=1, verbose_name="版本号")

    class Meta:
        verbose_name = "公开课题"
        verbose_name_plural = "公开课题"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (公开版本 v{self.version})"

    def delete(self, *args, **kwargs):
        """删除对象时同时删除关联的文件"""
        if self.description_file:
            # 删除文件
            self.description_file.delete(save=False)
        # 调用父类的delete方法
        super().delete(*args, **kwargs)
