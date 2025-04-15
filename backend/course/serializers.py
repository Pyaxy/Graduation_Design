from rest_framework import serializers
from .models import Course
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = ['user_id', 'name', 'role', 'role_display']

class CourseSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    students = UserSerializer(many=True, read_only=True)
    current_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'teacher', 'students', 
                 'course_code', 'status', 'current_status', 'created_at', 'updated_at',
                 'start_date', 'end_date']
        read_only_fields = ['course_code', 'created_at', 'updated_at']

    def get_current_status(self, obj):
        """获取当前状态"""
        return obj.calculate_status()

    def to_representation(self, instance):
        """在序列化时更新状态"""
        data = super().to_representation(instance)
        # 更新数据库中的状态
        instance.status = instance.calculate_status()
        instance.save(update_fields=['status'])
        return data


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['name', 'description', 'start_date', 'end_date']

    def create(self, validated_data):
        # 获取当前用户作为创建者
        user = self.context['request'].user
        validated_data['teacher'] = user
        return super().create(validated_data)
