from django.db import models
from accounts.models import User
import uuid
from django.utils import timezone

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