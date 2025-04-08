from rest_framework import status
from rest_framework.test import APITestCase
from subject.models import Subject
from accounts.models import User
from django.urls import reverse
'''
2. create 方法测试要求：
基础功能测试：
    使用有效数据创建课题
    创建成功后返回的数据格式是否正确
    创建后数据是否正确保存到数据库
数据验证测试：
    必填字段（title、description、max_students）缺失时的处理
    字段类型错误时的处理（比如 max_students 传字符串）
    字段长度/大小限制（比如 max_students 超出范围）
文件上传测试：
    上传有效的课题文件
    上传无效格式的文件
    不上传文件的情况
权限测试：
    未登录用户创建课题的响应
    学生创建课题的响应（应该被拒绝）
    教师创建课题（应该成功）
    管理员创建课题（应该成功）
业务逻辑测试：
    创建后的课题状态是否为 PENDING
    creator 字段是否正确设置为当前用户
    创建时间（created_at）是否正确设置
'''
class SubjectCreateTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """类级别的测试数据准备，只执行一次"""
        print("\n-----开始准备测试数据-----")
        
        # 清空数据库
        Subject.objects.all().delete()
        User.objects.all().delete()

        # 准备测试用户
        cls.teacher = User.objects.create_user(
            email="teacher@example.com", 
            password="teacher123", 
            user_id="teacher001", 
            name="teacher", 
            school="teacher school", 
            role="TEACHER"
        )
        cls.teacher2 = User.objects.create_user(
            email="teacher2@example.com", 
            password="teacher123", 
            user_id="teacher002", 
            name="teacher2", 
            school="teacher school", 
            role="TEACHER"
        )
        cls.student = User.objects.create_user(
            email="student@example.com", 
            password="student123", 
            user_id="student001", 
            name="student", 
            school="student school", 
            role="STUDENT"
        )
        cls.admin = User.objects.create_superuser(
            email="admin@example.com", 
            password="admin123", 
            user_id="admin001", 
            name="admin", 
            school="admin school", 
            role="ADMIN"
        )

        # url
        cls.url = reverse("subject-list")
        
        
        print("-----测试数据准备完成-----\n")
    
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        # 清空课题数据，保持数据库干净
        Subject.objects.all().delete()
        
        # 获取token
        self.teacher_token = self.client.post(
            reverse("login"), 
            {"email": self.teacher.email, "password": "teacher123"}
        ).data["data"]["access"]
        
        self.student_token = self.client.post(
            reverse("login"), 
            {"email": self.student.email, "password": "student123"}
        ).data["data"]["access"]
        
        self.admin_token = self.client.post(
            reverse("login"), 
            {"email": self.admin.email, "password": "admin123"}
        ).data["data"]["access"]
        
    def test_create_subject_with_valid_data(self):
        """测试使用有效数据创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "max_students": 10
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.title, "test_title")
        self.assertEqual(subject.description, "test_description")
        self.assertEqual(subject.max_students, 10)
        self.assertEqual(subject.creator, self.teacher)
        self.assertEqual(subject.status, "PENDING")
        self.assertIsNotNone(subject.created_at)
        
        
        