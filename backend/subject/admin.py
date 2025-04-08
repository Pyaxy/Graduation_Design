from django.contrib import admin
from .models import Subject

# Register your models here.
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'created_at')
    list_filter = ('status', 'creator')
    search_fields = ('title', 'description', 'creator__name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('creator', 'reviewer')
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'description_file', 'max_students')
        }),
        ('创建信息', {
            'fields': ('creator', 'created_at', 'updated_at')
        }),
        ('审核信息', {
            'fields': ('status', 'reviewer', 'review_comments')
        }),
    )
