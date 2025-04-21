from rest_framework.test import APITestCase
from subject.models import PublicSubject, Subject
from django.urls import reverse
from rest_framework import status
from accounts.models import User

MAX_SUBJECTS = 150
class PublicSubjectDeleteTestCase(APITestCase):
    # region 测试数据准备
    @classmethod
    def setUpTestData(cls):
        print("-----正在准备测试数据-----\n")
        # 清空数据库
        Subject.objects.all().delete()
        PublicSubject.objects.all().delete()
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

        # 申请url
        cls.url = reverse("public-subject-list")

        # 准备测试课题数据
        cls.subject_data_list = [{
            "title": f"test_title_{i}",
            "description": f"test_description_{i}",
            "languages": ["C", "CPP", "JAVA", "PYTHON"]
        } for i in range(1, MAX_SUBJECTS)]  # 修改这里，创建MAX_SUBJECTS个数据
        
        print("-----测试数据准备完成-----\n")
    def setUp(self):
        # 清空课题数据，保持数据库干净
        Subject.objects.all().delete()
        PublicSubject.objects.all().delete()
        
        # 获取token
        self.teacher_token = self.client.post(
            reverse("login"), 
            {"email": self.teacher.email, "password": "teacher123"}
        ).data["data"]["access"]

        self.teacher2_token = self.client.post(
            reverse("login"), 
            {"email": self.teacher2.email, "password": "teacher123"}
        ).data["data"]["access"]
        
        self.student_token = self.client.post(
            reverse("login"), 
            {"email": self.student.email, "password": "student123"}
        ).data["data"]["access"]
        
        self.admin_token = self.client.post(
            reverse("login"), 
            {"email": self.admin.email, "password": "admin123"}
        ).data["data"]["access"]

    def create_subjects(self, count=None, token=None):
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
                HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
            )


    def review_subjects(self, subject_id, status="APPROVED"):
        """审核课题"""
        return self.client.post(
            f"{reverse('subject-list')}{subject_id}/review/",
            data={
                "status": status,
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
    
    def apply_public(self, subject_id, token=None):
        """申请公开课题"""
        return self.client.post(
            f"{reverse('subject-list')}{subject_id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
        )
    
    def review_public(self, subject_id, token=None):
        """审核公开课题"""
        return self.client.post(
            f"{reverse('subject-list')}{subject_id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.admin_token}"
        )
    # endregion

    # region 测试删除
    def test_public_subject_delete_when_original_subject_is_deleted(self):
        """测试当原始课题被删除时，公开课题是否被删除"""
        # 创建原始课题
        self.create_subjects(1, token=self.teacher_token)
        self.review_subjects(Subject.objects.first().id, "APPROVED")
        self.apply_public(Subject.objects.first().id, token=self.teacher_token)
        self.review_public(Subject.objects.first().id, token=self.admin_token)
        # 删除原始课题
        self.client.delete(
            f"{reverse('subject-list')}{Subject.objects.first().id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 检查公开课题是否被删除
        self.assertEqual(PublicSubject.objects.count(), 0)

    # endregion