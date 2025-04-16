from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('user_id', 'email', 'name', 'school', 'role', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'role', 'school')
    search_fields = ('user_id', 'email', 'name')
    ordering = ('user_id',)
    
    fieldsets = (
        (None, {'fields': ('user_id', 'password')}),
        ('个人信息', {'fields': ('email', 'name', 'school', 'role')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_id', 'email', 'password1', 'password2', 'name', 'school', 'role'),
        }),
    )
