from rest_framework import status
from rest_framework.test import APITestCase
from subject.models import Subject
from accounts.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
'''
2. create 方法测试要求：
基础功能测试：
    使用有效数据创建课题
    创建成功后返回的数据格式是否正确
    创建后数据是否正确保存到数据库
数据验证测试：
    必填字段（title、description、languages）缺失时的处理
    字段类型错误时的处理（比如 languages 传字符串）
    字段长度/大小限制（比如 languages 超出范围）
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

    # region 数据准备
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
    # endregion
        
    # region 基础功能测试
    def test_create_subject_with_valid_data(self):
        """测试使用有效数据创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否有data和message
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.title, "test_title")
        self.assertEqual(subject.description, "test_description")
        self.assertEqual(subject.languages, ["C", "CPP", "PYTHON"])
        self.assertEqual(subject.creator, self.teacher)
        self.assertEqual(subject.status, "PENDING")
        self.assertIsNotNone(subject.created_at)
    # endregion
    
    # region 数据验证测试
    def test_create_subject_without_title(self):
        """测试使用无效数据创建课题"""
        data = {
            "description": "test_description",
            "languages": ["C", "CPP"]
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("title", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_subject_without_description(self):
        """测试使用无效数据创建课题"""
        data = {
            "title": "test_title",
            "languages": ["C", "CPP"]
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("description", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_subject_without_languages(self):
        """测试使用无效数据创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description"
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("languages", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_subject_with_invalid_languages(self):
        """测试使用无效的编程语言"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["INVALID_LANG"]
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("languages", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_subject_with_empty_languages(self):
        """测试使用空的编程语言列表"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": []
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("languages", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    # endregion
        
    # region 文件上传测试
    def test_create_subject_with_valid_file(self):
        """测试使用有效数据创建课题"""
        # 创建一个测试文件
        test_file = SimpleUploadedFile("test.txt", content=b"test", content_type="text/plain")
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"],
            "description_file": test_file
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        print(response.data)
        # 是否有data和message
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.title, "test_title")
        self.assertEqual(subject.description, "test_description")
        self.assertEqual(subject.languages, ["C", "CPP", "PYTHON"])
        self.assertEqual(subject.creator, self.teacher)
        self.assertEqual(subject.status, "PENDING")
        self.assertIsNotNone(subject.created_at)
        # 是否上传了文件
        self.assertIsNotNone(subject.description_file)
        # 文件是否被保存
        self.assertTrue(os.path.exists(subject.description_file.path))

        # 删除测试文件
        subject.delete()

    def test_create_subject_without_file(self):
        """测试创建课题时不上传文件"""
        print("================================================")

        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.title, "test_title")
        self.assertEqual(subject.description, "test_description")
        self.assertEqual(subject.languages, ["C", "CPP", "PYTHON"])
        self.assertEqual(subject.creator, self.teacher)
        self.assertEqual(subject.status, "PENDING")
        self.assertIsNotNone(subject.created_at)
        # 是否上传了文件
        self.assertFalse(subject.description_file)
        self.assertEqual(subject.description_file.name, '')
        print("================================================")


    def test_create_subject_with_invalid_file_format(self):
        """测试上传非允许格式文件"""
        # 创建一个非PDF格式的测试文件
        test_file = SimpleUploadedFile("test.jpg", b"test", content_type="image/jpeg")
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"],
            "description_file": test_file
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回正确的错误信息
        self.assertIn("只允许上传PDF、DOCX、DOC格式的文件", str(response.data))

    def test_delete_subject_with_file(self):
        """测试删除课题时是否同时删除文件"""
        # 创建一个带文件的课题
        test_file = SimpleUploadedFile("test.pdf", content=b"test", content_type="application/pdf")
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"],
            "description_file": test_file
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 获取创建的课题
        subject = Subject.objects.first()
        file_path = subject.description_file.path
        
        # 确认文件存在
        self.assertTrue(os.path.exists(file_path))
        
        # 删除课题
        subject.delete()
        
        # 确认文件已被删除
        self.assertFalse(os.path.exists(file_path))

    def test_create_subject_with_large_file(self):
        """测试上传超过大小限制的文件"""
        # 创建一个超过10MB的测试文件
        large_content = b"0" * (11 * 1024 * 1024)  # 11MB
        test_file = SimpleUploadedFile("test.pdf", large_content, content_type="application/pdf")
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"],
            "description_file": test_file
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回正确的错误信息
        self.assertIn("文件大小不能超过10MB", str(response.data))
    # endregion

    # region 权限测试
    def test_create_subject_without_login(self):
        """测试未登录用户创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart'
        )
        # 是否返回401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_subject_with_student(self):
        """测试学生创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        # 是否返回403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_subject_with_teacher(self):
        """测试教师创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.title, "test_title")
        self.assertEqual(subject.description, "test_description")
        self.assertEqual(subject.languages, ["C", "CPP", "PYTHON"])
        self.assertEqual(subject.creator, self.teacher)
        self.assertEqual(subject.status, "PENDING")
        self.assertIsNotNone(subject.created_at)

    def test_create_approved_subject_with_teacher(self):
        """测试教师创建已批准课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"],
            "status": "APPROVED"
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回正确的错误信息
        self.assertIn("课题状态不能为已批准", str(response.data["message"]))

    def test_create_rejected_subject_with_teacher(self):
        """测试教师创建已驳回课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"],
            "status": "REJECTED"
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回正确的错误信息
        self.assertIn("课题状态不能为已驳回", str(response.data["message"]))
        
    def test_create_subject_with_admin(self):
        """测试管理员创建课题"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.title, "test_title")
        self.assertEqual(subject.description, "test_description")
        self.assertEqual(subject.languages, ["C", "CPP", "PYTHON"])
        self.assertEqual(subject.creator, self.admin)
        self.assertEqual(subject.status, "PENDING")
        self.assertIsNotNone(subject.created_at)
    # endregion

    # region 业务逻辑测试
    def test_create_subject_status_pending(self):
        """测试创建课题时状态为PENDING"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.status, "PENDING")
    
    def test_create_subject_creator_field(self):
        """测试创建课题时creator字段正确设置"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.creator, self.teacher)
    
    def test_create_subject_created_at_field(self):
        """测试创建课题时created_at字段正确设置"""
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "PYTHON"]
        }
        response = self.client.post(
            self.url,
            data=data,
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertIsNotNone(subject.created_at)
    # endregion
    