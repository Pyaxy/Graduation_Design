from django.db import models
from accounts.models import User

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

    title = models.CharField(max_length=100, verbose_name="课题标题")
    description = models.TextField(verbose_name="课题描述")
    description_file = models.FileField(upload_to='subject_files/', verbose_name="课题原始描述文件", blank=True, null=True)
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="created_subjects",
        verbose_name="创建者",
        limit_choices_to={'role__in': ['TEACHER', 'ADMIN']}
    )
    max_students = models.PositiveIntegerField(default=1, verbose_name="最大学生数量")
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

    class Meta:
        verbose_name = "课题"
        verbose_name_plural = "课题"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
