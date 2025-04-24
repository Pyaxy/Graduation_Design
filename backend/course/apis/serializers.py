from rest_framework import serializers
from ..models import Course, Group, CourseSubject
from accounts.models import User
from django.http import Http404
from subject.api.serializers import SubjectSerializer, PublicSubjectSerializer
import uuid

# region 用户序列化器
class UserSerializer(serializers.ModelSerializer):
    '''用户序列化器'''
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = ['user_id', 'name', 'role', 'role_display']
# endregion

# region 课程序列化器

    # region 课程通用序列化器
class CourseSerializer(serializers.ModelSerializer):
    '''课程序列化器'''
    teacher = UserSerializer(read_only=True)
    students = UserSerializer(many=True, read_only=True)
    current_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'teacher', 'students', 
                 'course_code', 'status', 'current_status', 'created_at', 'updated_at',
                 'start_date', 'end_date', 'max_group_size', 'min_group_size']
        read_only_fields = ['id', 'course_code', 'status', 'created_at', 'updated_at', 'teacher', 'max_group_size', 'min_group_size'] 

    def validate(self, data):
        """验证开始时间不得比结束时间迟"""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("开始时间不得比结束时间迟")
        return data
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
    # endregion



    # region 课程创建序列化器
class CourseCreateSerializer(serializers.ModelSerializer):
    '''课程创建序列化器'''
    class Meta:
        model = Course
        fields = ['name', 'description', 'start_date', 'end_date', 'max_group_size', 'min_group_size']
        extra_kwargs = {
            'name': {'required': True},
            'description': {'required': False},  # 修改为可选
            'start_date': {'required': True},
            'end_date': {'required': True},
            'max_group_size': {'required': True},
            'min_group_size': {'required': True}
        }
    
    def validate(self, data):
        """验证开始时间不得比结束时间迟"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("开始时间不得比结束时间迟")
        if data['max_group_size'] < data['min_group_size']:
            raise serializers.ValidationError("最大小组人数不得小于最小小组人数")
        return data

    def create(self, validated_data):
        # 获取当前用户作为创建者
        user = self.context['request'].user
        validated_data['teacher'] = user
        return super().create(validated_data)
    # endregion



    # region 加入课程序列化器
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
    
class LeaveCourseSerializer(serializers.Serializer):
    '''退出课程序列化器'''
    student_user_id = serializers.CharField(required=True)
    class Meta:
        model = Course
        fields = ['student_user_id']
        read_only_fields = ['student_user_id']

    def validate_student_user_id(self, value):
        '''验证学生用户ID'''
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("学生用户ID不存在")
        return value
    # endregion

# endregion

# region 小组序列化器



    # region 小组通用序列化器
class GroupSerializer(serializers.ModelSerializer):
    '''小组序列化器'''
    creator = UserSerializer(read_only=True)
    students = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Group
        fields = ['id', 'name', 'course', 'students', 'creator', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'course', 'creator']
    # endregion

    # region 小组创建序列化器
class GroupCreateSerializer(serializers.ModelSerializer):
    '''小组创建序列化器'''
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=True)
    class Meta:
        model = Group
        fields = ['course']
    
    def create(self, validated_data):
        '''创建小组'''
        user = self.context['request'].user
        validated_data['max_students'] = validated_data['course'].max_group_size
        validated_data['min_students'] = validated_data['course'].min_group_size
        group = Group.objects.create(creator=user, **validated_data)
        if user.role == 'STUDENT':
            group.students.add(user)
        return group
    # endregion

    # region 退出小组序列化器
class LeaveGroupSerializer(serializers.Serializer):
    """退出小组序列化器"""
    student_user_id = serializers.CharField(required=True)

    class Meta:
        model = Group
        fields = ['student_user_id']
        read_only_fields = ['student_user_id']

    def validate_student_user_id(self, value):
        '''验证学生用户ID'''
        if not User.objects.filter(user_id=value).exists():
            raise Http404("学生用户ID不存在")
        return value
    # endregion

    # region 小组列表序列化器
class GroupListSerializer(serializers.ModelSerializer):
    '''小组列表序列化器'''
    class Meta:
        model = Group
        fields = ['id', 'name', 'course', 'students', 'creator', 'created_at', 'updated_at']
    # endregion



# endregion



# region 课程的课题序列化器
class AddSubjectSerializer(serializers.Serializer):
    """添加课题序列化器"""
    subject_ids = serializers.CharField(required=True, help_text="课题ID列表，用逗号分隔")
    subject_type = serializers.ChoiceField(choices=['PRIVATE', 'PUBLIC'], required=True)

    def validate_subject_ids(self, value):
        """验证subject_ids格式"""
        try:
            ids = [int(id.strip()) for id in value.split(',') if id.strip()]
            if not ids:
                raise serializers.ValidationError("课题ID列表不能为空")
            return ids
        except ValueError:
            raise serializers.ValidationError("课题ID必须是数字")

class SubjectBaseSerializer(serializers.Serializer):
    """课题基础序列化器"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

class CourseSubjectSerializer(serializers.Serializer):
    """课程课题序列化器"""
    id = serializers.UUIDField()
    subject = serializers.SerializerMethodField()
    subject_type = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    class Meta:
        model = CourseSubject
        fields = ['id', 'subject', 'subject_type', 'created_at', 'updated_at']

    def get_subject(self, obj):
        """根据课题类型选择不同的序列化器"""
        if obj.subject_type == 'PRIVATE':
            return SubjectSerializer(obj.private_subject, context=self.context).data
        else:
            return PublicSubjectSerializer(obj.public_subject, context=self.context).data

class DeleteSubjectSerializer(serializers.Serializer):
    """删除课题序列化器"""
    course_subject_id = serializers.UUIDField(required=True, help_text="要删除的课程课题ID")

    def validate_course_subject_id(self, value):
        """验证course_subject_id格式"""
        try:
            uuid.UUID(str(value))
            return value
        except ValueError:
            raise serializers.ValidationError("无效的UUID格式")




# endregion