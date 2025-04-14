from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'status', 'course_code', 'start_date', 'end_date')
    list_filter = ('status', 'teacher')
    search_fields = ('name', 'course_code', 'teacher__username')
    filter_horizontal = ('students',)
