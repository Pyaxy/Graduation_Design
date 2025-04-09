'''
课题更新测试
'''

from rest_framework.test import APITestCase
from rest_framework import status
from subject.models import Subject
from accounts.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os

MAX_SUBJECTS = 150

class SubjectUpdateTestCase(APITestCase):

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

        # 删除url
        cls.url = reverse("subject-list")

        # 准备测试课题数据
        cls.subject_data_list = [{
            "title": f"test_title_{i}",
            "description": f"test_description_{i}",
            "max_students": i
        } for i in range(1, MAX_SUBJECTS)]  # 修改这里，创建MAX_SUBJECTS个数据
        
        
        
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
    
    def create_subjects(self, count=None, creator=None, status="PENDING"):
        """批量创建测试课题"""
        data_to_create = self.subject_data_list[:count] if count else self.subject_data_list
        subjects = [
            Subject(
                title=data["title"],
                description=data["description"],
                max_students=data["max_students"],
                creator=creator,
                status=status
            ) for data in data_to_create
        ]
        return Subject.objects.bulk_create(subjects)
    # endregion

    # region 正常更新测试
    def test_update_subject_with_valid_data(self):
        """更新课题成功"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        before_update_time = subject.updated_at
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.title, "updated_title")
        self.assertEqual(subject.description, "updated_description")
        self.assertEqual(subject.max_students, 10)
        self.assertEqual(subject.status, "PENDING")
        # 更新时间是否变化
        self.assertNotEqual(subject.updated_at, before_update_time)

    def test_update_rejected_subject_with_valid_data(self):
        """更新之后，课题状态变为PENDING"""
        self.create_subjects(1, self.teacher, "REJECTED")
        subject = Subject.objects.first()
        before_update_time = subject.updated_at
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.title, "updated_title")
        self.assertEqual(subject.description, "updated_description")
        self.assertEqual(subject.max_students, 10)
        self.assertEqual(subject.status, "PENDING")
        # 更新时间是否变化
        self.assertNotEqual(subject.updated_at, before_update_time)

    def test_update_approved_subject_with_valid_data(self):
        """更新之后，课题状态变为PENDING"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        before_update_time = subject.updated_at
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.title, "updated_title")
        self.assertEqual(subject.description, "updated_description")
        self.assertEqual(subject.max_students, 10)
        self.assertEqual(subject.status, "PENDING")
        # 更新时间是否变化
        self.assertNotEqual(subject.updated_at, before_update_time)
    
    # endregion

    # region 必填字段测试
    def test_update_subject_without_title(self):
        """更新课题时，缺少必填字段title"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data["message"])
    
    def test_update_subject_without_description(self):
        """更新课题时，缺少必填字段description"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data["message"])
    # endregion

    # region 字段类型测试
    def test_update_subject_with_invalid_max_students(self):
        """更新课题时，max_students字段类型错误"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": "invalid_max_students"
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_students", response.data["message"])
    # endregion

    # region 字段长度/大小限制测试
    def test_update_subject_with_long_title(self):
        """更新课题时，title字段长度超过限制"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "a" * 101,
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data["message"])
    # endregion
    
    # region 文件处理测试
    def test_update_subject_with_file(self):
        """更新课题时，上传文件"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10,
            "description_file": SimpleUploadedFile("test.txt", content=b"test", content_type="text/plain")
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertIn("test.txt", subject.description_file.name)
        self.assertTrue(os.path.exists(subject.description_file.path))

        subject.description_file.delete()

    def test_update_subject_without_file(self):
        """更新课题时，不上传文件"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.description_file.name, "")

    def test_update_subject_with_large_file(self):
        """更新课题时，上传大文件"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10,
            "description_file": SimpleUploadedFile("large_file.txt", content=b"a" * 1024 * 1024 * 11, content_type="text/plain")
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description_file", response.data["message"])

    def test_update_subject_with_invalid_file_format(self):
        """更新课题时，上传无效的文件格式"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10,
            "description_file": SimpleUploadedFile("invalid_file.png", content=b"invalid", content_type="image/png")
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description_file", response.data["message"])
    # endregion
    
    # region 权限测试
    def test_update_subject_without_token(self):
        """更新课题时，未授权用户尝试更新"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_approved_subject_with_unauthorized_user(self):
        """更新课题时，未授权用户尝试更新已审核课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_pending_subject_with_unauthorized_user(self):
        """更新课题时，未授权用户尝试更新待审核课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_subject_with_teacher_update_his_subject(self):
        """更新课题时，教师用户尝试更新自己的课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.title, "updated_title")
        self.assertEqual(subject.description, "updated_description")
        self.assertEqual(subject.max_students, 10)
    
    def test_update_subject_with_teacher_update_other_teacher_subject(self):
        """更新课题时，教师用户尝试更新其他教师的课题"""
        self.create_subjects(1, self.teacher2, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_subject_with_admin_update_subject(self):
        """更新课题时，管理员用户尝试更新课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}{subject.id}/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.title, "updated_title")
        self.assertEqual(subject.description, "updated_description")
        self.assertEqual(subject.max_students, 10)
    # endregion
    
    # region 数据验证测试
    def test_update_subject_with_invalid_subject_id(self):
        """更新课题时，使用无效的课题ID"""
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }   
        response = self.client.put(
            f"{self.url}invalid_id/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)   
        
    def test_update_subject_with_deleted_subject(self):
        """更新课题时，使用已删除的课题ID"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        subject.delete()
        update_data = {
            "title": "updated_title",
            "description": "updated_description",
            "max_students": 10
        }
        response = self.client.put(
            f"{self.url}invalid_id/",
            data=update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
    
    
    
    
