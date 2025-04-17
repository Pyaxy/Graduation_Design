from django.contrib import admin
from .models import Course, Group

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'status', 'course_code', 'start_date', 'end_date')
    list_filter = ('status', 'teacher')
    search_fields = ('name', 'course_code', 'teacher__username')
    filter_horizontal = ('students',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'creator', 'created_at', 'updated_at')
    list_filter = ('course', 'creator')
    search_fields = ('name', 'course__name', 'creator__username')
    filter_horizontal = ('students',)