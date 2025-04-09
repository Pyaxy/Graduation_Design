from rest_framework.test import APITestCase
from rest_framework import status
from subject.models import Subject
from accounts.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
'''
课题审核测试
'''
MAX_SUBJECTS = 150

class SubjectReviewTestCase(APITestCase):
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
    
    # region 审核测试
    def test_review_subject_with_admin_approved_subject(self):
        """管理员审核通过课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.status, "APPROVED")
        self.assertEqual(subject.review_comments, "审核通过")
        self.assertEqual(subject.reviewer, self.admin)

        self.assertIn("审核通过", response.data["data"]['review_comments'])

    def test_review_subject_with_admin_rejected_subject(self):
        """管理员审核拒绝课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "REJECTED",
                "review_comments": "审核拒绝"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.status, "REJECTED")
        self.assertEqual(subject.review_comments, "审核拒绝")
        self.assertEqual(subject.reviewer, self.admin)

        self.assertIn("审核拒绝", response.data["data"]['review_comments'])

    def test_review_subject_with_teacher_approved_subject(self):
        """教师审核课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_subject_with_teacher_rejected_subject(self):
        """教师审核拒绝课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "REJECTED",
                "review_comments": "审核拒绝"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        subject.refresh_from_db()
        self.assertEqual(subject.status, "PENDING")
        self.assertEqual(subject.review_comments, None)
        self.assertEqual(subject.reviewer, None)

    def test_review_subject_with_student_approved_subject(self):
        """学生审核通过课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_review_subject_with_student_rejected_subject(self):
        """学生审核拒绝课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        # 学生应该看不到 PENDING 状态的课题
        response = self.client.get(
            f"{self.url}",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(len(response.data["data"]["results"]), 0)  # 确认学生看不到任何课题
        
        # 尝试审核（即使知道 ID 也应该返回 404）
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "REJECTED",
                "review_comments": "审核拒绝"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_review_subject_with_unauthorized_user(self):
        """未授权用户审核课题"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    # endregion

    # region 数据验证测试
    def test_review_subject_with_invalid_subject_id(self):
        """无效课题ID"""
        response = self.client.post(
            f"{self.url}999999/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_review_subject_with_deleted_subject(self):
        """删除课题后审核"""
        self.create_subjects(1, self.teacher, "PENDING")
        id = Subject.objects.first().id
        subject = Subject.objects.first()
        subject.delete()
        response = self.client.post(
            f"{self.url}{id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_review_subject_with_invalid_status(self):
        """无效状态"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "INVALID",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )   
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_subject_with_empty_status(self):
        """空状态"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_review_subject_with_empty_review_comments(self):
        """空审核备注"""
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": ""
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    # endregion
    
    # region 边界测试
    def test_review_approved_subject(self):
        """审核已通过课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.status, "APPROVED")

    def test_review_rejected_subject(self):
        """审核已拒绝课题"""
        self.create_subjects(1, self.teacher, "REJECTED")
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.status, "APPROVED")

    def test_review_not_exist_subject(self):
        """不存在课题"""
        response = self.client.post(
            f"{self.url}999999/review/",
            data={
                "status": "APPROVED",
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
    