from rest_framework import serializers
from accounts.models import User
from subject.models import Subject


class UserSerializer(serializers.ModelSerializer):
    """简略版用户序列化器，用于嵌套显示"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['user_id', 'name', 'role', 'role_display']
        read_only_fields = fields


class SubjectSerializer(serializers.ModelSerializer):
    """课题序列化器"""
    creator = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    description_file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id', 'title', 'description', 'description_file', 'description_file_url', 'creator',
            'max_students', 'status', 'status_display', 'reviewer',
            'review_comments', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'status_display', 'reviewer',
            'review_comments', 'created_at', 'updated_at'
        ]
        
    def get_description_file_url(self, obj):
        """获取文件的完整URL"""
        if obj.description_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.description_file.url)
            return obj.description_file.url
        return None


class SubjectCreateSerializer(serializers.ModelSerializer):
    """课题创建序列化器"""

    class Meta:
        model = Subject
        fields = [
            'title', 'description', 'description_file', 'max_students'
        ]

    def create(self, validated_data):
        # 获取当前用户作为创建者
        user = self.context['request'].user
        validated_data['creator'] = user
        return super().create(validated_data)


class SubjectReviewSerializer(serializers.ModelSerializer):
    """课题审核序列化器"""
    
    class Meta:
        model = Subject
        fields = ['status', 'review_comments']
        
    def validate(self, attrs):
        """验证所有字段"""
        if attrs.get('status') == "":
            raise serializers.ValidationError({"status": "课题状态不能为空"})
        if attrs.get('status') not in [choice[0] for choice in Subject.STATUS_CHOICES]:
            raise serializers.ValidationError({"status": "无效的课题状态"})
        return attrs
        
    def update(self, instance, validated_data):
        # 获取当前用户作为审核人
        user = self.context['request'].user
        if user.role != 'ADMIN':
            raise serializers.ValidationError("只有管理员可以审核课题")
        
        # 设置审核人
        validated_data['reviewer'] = user
        
        # 只允许修改审核状态和审核意见
        instance.status = validated_data.get('status', instance.status)
        instance.review_comments = validated_data.get('review_comments', instance.review_comments)
        instance.reviewer = validated_data.get('reviewer', instance.reviewer)
        instance.save()
        
        return instance 