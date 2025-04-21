from rest_framework.test import APITestCase
from rest_framework import status
from subject.models import Subject
from accounts.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

'''
测试课题详情页的获取
'''
MAX_SUBJECTS = 150
class SubjectRetrieveTestCase(APITestCase):

    # region 测试数据准备
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
            "languages": ["C", "CPP", "JAVA", "PYTHON"]
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
        for data in data_to_create:
            self.client.post(
                reverse("subject-list"),
                data={
                "title": data["title"],
                "description": data["description"],
                "languages": data["languages"],
                },
                HTTP_AUTHORIZATION=f"Bearer {self.teacher_token if creator == self.teacher else self.admin_token}"
            )
    
    def create_all_subjects(self):
        """创建所有测试课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        self.create_subjects(1, self.teacher, "PENDING")
        self.create_subjects(1, self.teacher, "REJECTED")
        self.create_subjects(1, self.teacher2, "APPROVED")
        self.create_subjects(1, self.teacher2, "PENDING")
        self.create_subjects(1, self.teacher2, "REJECTED")
        self.create_subjects(1, self.admin, "APPROVED")
        self.create_subjects(1, self.admin, "PENDING")
        self.create_subjects(1, self.admin, "REJECTED")
        
        
    # endregion

    # region 基本功能测试
    def test_admin_can_view_all_subjects(self):
        """管理员可以查看所有课题"""
        self.create_all_subjects()
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["data"]["title"], subject.title)
            self.assertEqual(response.data["data"]["description"], subject.description)
            self.assertEqual(response.data["data"]["languages"], subject.languages)
            self.assertEqual(response.data["data"]["creator"]["user_id"], subject.creator.user_id)
            self.assertEqual(response.data["data"]["status"], subject.status)
            self.assertEqual(response.data["data"]["status_display"], subject.get_status_display())
            self.assertEqual(response.data["data"]["reviewer"]["user_id"] if response.data["data"]["reviewer"] else None, subject.reviewer.user_id if subject.reviewer else None)
            self.assertEqual(response.data["data"]["review_comments"], subject.review_comments)
        
    def test_teacher_can_view_his_subjects(self):
        """教师可以查看自己的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        self.create_subjects(1, self.teacher, "PENDING")
        self.create_subjects(1, self.teacher, "REJECTED")
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["data"]["title"], subject.title)
            self.assertEqual(response.data["data"]["description"], subject.description)
            self.assertEqual(response.data["data"]["languages"], subject.languages)
            self.assertEqual(response.data["data"]["creator"]["user_id"], subject.creator.user_id)
            self.assertEqual(response.data["data"]["status"], subject.status)
            self.assertEqual(response.data["data"]["status_display"], subject.get_status_display())
            self.assertEqual(response.data["data"]["reviewer"]["user_id"] if response.data["data"]["reviewer"] else None, subject.reviewer.user_id if subject.reviewer else None)
            self.assertEqual(response.data["data"]["review_comments"], subject.review_comments)

    def test_teacher_can_view_approved_subjects(self):
        """教师可以查看自己的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["data"]["title"], subject.title)
            self.assertEqual(response.data["data"]["description"], subject.description)
            self.assertEqual(response.data["data"]["languages"], subject.languages)
            self.assertEqual(response.data["data"]["creator"]["user_id"], subject.creator.user_id)
            self.assertEqual(response.data["data"]["status"], subject.status)
            self.assertEqual(response.data["data"]["status_display"], subject.get_status_display())
            self.assertEqual(response.data["data"]["reviewer"]["user_id"] if response.data["data"]["reviewer"] else None, subject.reviewer.user_id if subject.reviewer else None)
            self.assertEqual(response.data["data"]["review_comments"], subject.review_comments)
            
    def test_student_can_view_approved_subjects(self):
        """学生可以无法查看未公开的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        self.create_subjects(1, self.teacher2, "APPROVED")
        self.create_subjects(1, self.admin, "APPROVED")
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # endregion

    # region 权限测试
    def test_unlogin_user_cannot_view_subjects(self):
        """未登录用户不能查看课题"""
        self.create_all_subjects()
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_teacher_cannot_view_other_teacher_pending_and_rejected_subjects(self):
        """教师不能查看其他教师待审核和驳回的课题"""
        self.create_subjects(1, self.teacher2, "PENDING")
        self.create_subjects(1, self.teacher2, "REJECTED")
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_view_pending_and_rejected_subjects(self):
        """学生不能查看待审核和驳回的课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        self.create_subjects(1, self.teacher, "REJECTED")
        self.create_subjects(1, self.teacher2, "PENDING")
        self.create_subjects(1, self.teacher2, "REJECTED")
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion

    # region 数据完整性测试
    def test_subject_data_integrity(self):
        """课题数据完整性测试"""
        self.create_all_subjects()
        file = SimpleUploadedFile("test.txt", b"test", content_type="text/plain")
        self.client.post(
            f"{self.url}",
            format="multipart",
            data={
                "title": "test_title",
                "description": "test_description",
                "languages": ["C", "CPP", "JAVA", "PYTHON"],
                "description_file": file
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        for subject in Subject.objects.all():
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["data"]["id"], subject.pk)
            self.assertEqual(response.data["data"]["title"], subject.title)
            self.assertEqual(response.data["data"]["description"], subject.description)
            if subject.description_file:
                self.assertIn(subject.description_file.url, response.data["data"]["description_file"])
            else:
                self.assertEqual(response.data["data"]["description_file"], None)
            self.assertEqual(response.data["data"]["languages"], subject.languages)
            self.assertEqual(response.data["data"]["creator"]["user_id"], subject.creator.user_id)
            self.assertEqual(response.data["data"]["creator"]["name"], subject.creator.name)
            self.assertEqual(response.data["data"]["creator"]["role"], subject.creator.role)
            self.assertEqual(response.data["data"]["creator"]["role_display"], subject.creator.get_role_display())
            self.assertEqual(response.data["data"]["status"], subject.status)
            self.assertEqual(response.data["data"]["status_display"], subject.get_status_display())
            self.assertEqual(response.data["data"]["reviewer"]["user_id"] if response.data["data"]["reviewer"] else None, subject.reviewer.user_id if subject.reviewer else None)
            self.assertEqual(response.data["data"]["reviewer"]["name"] if response.data["data"]["reviewer"] else None, subject.reviewer.name if subject.reviewer else None)
            self.assertEqual(response.data["data"]["reviewer"]["role"] if response.data["data"]["reviewer"] else None, subject.reviewer.role if subject.reviewer else None)
            self.assertEqual(response.data["data"]["reviewer"]["role_display"] if response.data["data"]["reviewer"] else None, subject.reviewer.get_role_display() if subject.reviewer else None)
            self.assertEqual(response.data["data"]["review_comments"], subject.review_comments)
            subject.delete()

    # endregion

    # region 异常情况测试
    def test_retrieve_not_exist_subject(self):
        """获取不存在课题"""
        response = self.client.get(
            f"{self.url}999999/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_deleted_subject(self):
        """获取已删除课题"""
        self.create_all_subjects()
        for subject in Subject.objects.all():
            subject.delete()
            response = self.client.get(
                f"{self.url}{subject.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            
    def test_retrieve_subject_with_invalid_id(self):
        """获取无效课题ID"""
        response = self.client.get(
            f"{self.url}invalid_id/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion