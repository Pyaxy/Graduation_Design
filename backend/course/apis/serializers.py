from rest_framework import serializers
from ..models import Course
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    '''用户序列化器'''
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = ['user_id', 'name', 'role', 'role_display']

class CourseSerializer(serializers.ModelSerializer):
    '''课程序列化器'''
    teacher = UserSerializer(read_only=True)
    students = UserSerializer(many=True, read_only=True)
    current_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'teacher', 'students', 
                 'course_code', 'status', 'current_status', 'created_at', 'updated_at',
                 'start_date', 'end_date']
        read_only_fields = ['id', 'course_code', 'status', 'created_at', 'updated_at', 'teacher']

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
    '''课程创建序列化器'''
    class Meta:
        model = Course
        fields = ['name', 'description', 'start_date', 'end_date']
        extra_kwargs = {
            'name': {'required': True},
            'description': {'required': False},  # 修改为可选
            'start_date': {'required': True},
            'end_date': {'required': True}
        }

    def create(self, validated_data):
        # 获取当前用户作为创建者
        user = self.context['request'].user
        validated_data['teacher'] = user
        return super().create(validated_data)
    
class JoinCourseSerializer(serializers.Serializer):
    '''加入课程序列化器'''
    course_code = serializers.CharField(required=True)
    class Meta:
        model = Course
        fields = ['course_code']
        read_only_fields = ['course_code']

    def validate_course_code(self, value):
        '''验证课程码'''
        if not Course.objects.filter(course_code=value).exists():
            raise serializers.ValidationError("课程码不存在")
        return value
