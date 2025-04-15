from django.db import models
from accounts.models import User
import uuid
from django.utils import timezone

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
