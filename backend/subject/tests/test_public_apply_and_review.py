from rest_framework.test import APITestCase
from rest_framework import status
from subject.models import Subject
from subject.models import PublicSubject
from accounts.models import User
from django.urls import reverse

MAX_SUBJECTS = 150
class SubjectPublicTestCase(APITestCase):
    # region 测试数据准备
    @classmethod
    def setUpTestData(cls):
        print("-----正在准备测试数据-----\n")
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

        # 申请url
        cls.url = reverse("subject-list")

        # 准备测试课题数据
        cls.subject_data_list = [{
            "title": f"test_title_{i}",
            "description": f"test_description_{i}",
            "max_students": i
        } for i in range(1, MAX_SUBJECTS)]  # 修改这里，创建MAX_SUBJECTS个数据
        
        print("-----测试数据准备完成-----\n")
    def setUp(self):
        # 清空课题数据，保持数据库干净
        Subject.objects.all().delete()
        
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
                "max_students": data["max_students"],
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
    # endregion

# region 申请测试
    # region 正常申请测试
    def test_public_subject_apply(self):
        """测试公共课题申请"""
        self.create_subjects(count=1, token=self.teacher_token) 
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.public_status, "PENDING")
        self.assertEqual(subject.is_public, False)
    # endregion
    
    # region 异常字段测试
    def test_public_subject_apply_without_subject_id(self):
        """测试申请公共课题时缺少subject_id"""
        response = self.client.post(
            f"{self.url}/apply-public/",
            data={},
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_subject_apply_with_invalid_subject_id(self):
        """测试申请公共课题时使用无效的subject_id"""
        response = self.client.post(
            f"{self.url}123345/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_subject_apply_with_unapproved_subject(self):
        """测试申请公共课题时使用未审核的课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_subject_apply_with_already_public_subject(self):
        """测试申请公共课题时使用已公开的课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        self.apply_public(subject.id, token=self.teacher_token)
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    # endregion

    # region 权限测试
    def test_public_subject_apply_with_student(self):
        """测试学生申请公开课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_subject_apply_with_admin(self):
        """测试管理员申请公开课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.public_status, "PENDING")
        self.assertEqual(subject.is_public, False)

    def test_public_subject_apply_with_unauthorized_user(self):
        """测试未授权用户申请公开课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_public_subject_apply_with_teacher_apply_other_teacher_subject(self):
        """测试教师申请其他教师课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        response = self.client.post(
            f"{self.url}{subject.id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
    
# region 审核测试
    # region 正常审核测试
    def test_public_subject_review(self):
        """测试公共课题审核"""
        # 申请课题
        self.test_public_subject_apply()
        subject = Subject.objects.first()
        # 审核课题
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.public_status, "APPROVED")
        self.assertEqual(subject.is_public, True)
        self.assertEqual(subject.public_reviewer, self.admin)
        self.assertEqual(subject.public_review_comments, "审核通过")
    # endregion

    # region 异常字段测试
    def test_public_subject_review_without_subject_id(self):
        """测试审核公共课题时缺少subject_id"""
        response = self.client.post(
            f"{self.url}/review-public/",
            data={},
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_subject_review_with_invalid_subject_id(self):
        """测试审核公共课题时使用无效的subject_id"""
        response = self.client.post(
            f"{self.url}123345/review-public/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_subject_review_without_public_status(self):
        """测试审核公共课题时缺少public_status"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_subject_review_with_invalid_public_status(self):
        """测试审核公共课题时使用无效的public_status"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "INVALID",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )   
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_subject_review_with_unapproved_subject(self):
        """测试审核公共课题时使用未审核的课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_subject_review_with_status(self):
        """测试审核公共课题时使用status"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过",
                "status": "APPROVED"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_subject_review_with_not_applied_subject(self):
        """测试审核公共课题时使用未申请的课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    # endregion

    # region 权限测试
    def test_public_subject_review_with_student(self):
        """测试学生审核公共课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_subject_review_with_admin(self):
        """测试管理员审核公共课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        self.apply_public(subject.id, token=self.teacher_token)
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subject.refresh_from_db()
        self.assertEqual(subject.public_status, "APPROVED")
        self.assertEqual(subject.is_public, True)
        self.assertEqual(subject.public_reviewer, self.admin)
        self.assertEqual(subject.public_review_comments, "审核通过")

    def test_public_subject_review_with_unauthorized_user(self):
        """测试未授权用户审核公共课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_public_subject_review_with_teacher_review_his_subject(self):
        """测试教师审核自己的课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_subject_review_with_teacher_review_other_teacher_subject(self):
        """测试教师审核其他教师的课题"""
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        response = self.client.post(
            f"{self.url}{subject.id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
# endregion