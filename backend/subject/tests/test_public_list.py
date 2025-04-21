from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from accounts.models import User
from subject.models import Subject, PublicSubject
from django.core.files.uploadedfile import SimpleUploadedFile
import os
MAX_SUBJECTS = 150
class PublicSubjectTestCase(APITestCase):
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


    # region 正常测试
    def test_public_subject_list_with_admin(self):
        """测试管理员查看公共课题列表"""
        self.create_subjects(count=3, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 3)
        self.assertEqual(len(response.data["data"]["results"]), 3)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

        # 检查返回数据
        for subject in response.data["data"]["results"]:
            self.assertEqual(subject["creator"]["user_id"], self.teacher.user_id)
            self.assertIsNotNone(subject["description"])
            self.assertIsNotNone(subject["title"])
            self.assertIsNotNone(subject["languages"])
            self.assertIsNotNone(subject["created_at"])
            self.assertIsNotNone(subject["id"])

    def test_public_subject_list_with_teacher(self):
        """测试教师查看公共课题列表"""
        self.create_subjects(count=3, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 3)
        self.assertEqual(len(response.data["data"]["results"]), 3)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

        # 检查返回数据
        for subject in response.data["data"]["results"]:
            self.assertEqual(subject["creator"]["user_id"], self.teacher.user_id)
            self.assertIsNotNone(subject["description"])
            self.assertIsNotNone(subject["title"])
            self.assertIsNotNone(subject["languages"])
            self.assertIsNotNone(subject["created_at"])
            self.assertIsNotNone(subject["id"])
    
    def test_public_subject_list_with_student(self):
        """测试学生查看公共课题列表"""
        self.create_subjects(count=3, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 3)
        self.assertEqual(len(response.data["data"]["results"]), 3)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

        # 检查返回数据
        for subject in response.data["data"]["results"]:
            self.assertEqual(subject["creator"]["user_id"], self.teacher.user_id)
            self.assertIsNotNone(subject["description"])
            self.assertIsNotNone(subject["title"])
            self.assertIsNotNone(subject["languages"])
            self.assertIsNotNone(subject["created_at"])
            self.assertIsNotNone(subject["id"])

    def test_public_subject_list_with_admin_empty_database(self):
        """测试管理员查看空数据库"""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_teacher_empty_database(self):
        """测试教师查看空数据库"""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_student_empty_database(self):
        """测试学生查看空数据库"""
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion

    # region 分页测试
    def test_public_subject_list_with_admin_paginated_subjects_num_less_or_equal_than_page_size(self):
        """测试管理员查看公共课题列表，数量小于等于每页数量"""
        self.create_subjects(count=3, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            f"{self.url}?page=1&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 3)
        self.assertEqual(len(response.data["data"]["results"]), 3)

        # 检查下一页和上一页
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_visit_page_1(self):
        """测试管理员查看公共课题列表，数量大于每页数量，访问第一页"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            f"{self.url}?page=1&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 10)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_visit_page_2(self):
        """测试管理员查看公共课题列表，数量大于每页数量，访问第二页"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            f"{self.url}?page=2&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 1)

        # 检查下一页和上一页
        self.assertEqual(response.data["data"]["next"], None)
        self.assertNotIn("page=1", response.data["data"]["previous"])

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_and_page_is_not_int_and_page_size_is_not_int(self):
        """测试管理员查看公共课题列表，数量大于每页数量，页码不是整数，每页数量不是整数"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?page=1.5&page_size=a",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_and_visit_last_page(self):
        """测试管理员查看公共课题列表，数量大于每页数量，访问最后一页"""
        self.create_subjects(count=25, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)

        response = self.client.get(
            f"{self.url}?page=3&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 25)
        self.assertEqual(len(response.data["data"]["results"]), 5)

        # 检查下一页和上一页
        self.assertEqual(response.data["data"]["next"], None)
        self.assertIn("page=2", response.data["data"]["previous"])

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_and_visit_midlle_page(self):
        """测试管理员查看公共课题列表，数量大于每页数量，访问中间页"""
        self.create_subjects(count=25, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 25)
        self.assertEqual(len(response.data["data"]["results"]), 10)

        # 检查下一页和上一页
        self.assertIn("page=3", response.data["data"]["next"])
        self.assertNotIn("page=1", response.data["data"]["previous"])

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_admin_paginated_subjects_and_visit_page_not_exist(self):
        """测试管理员查看公共课题列表，数量大于每页数量，访问不存在的页码"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?page=4&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_and_page_size_is_bigger_than_10(self):
        """测试管理员查看公共课题列表，数量大于每页数量，每页数量大于10"""
        self.create_subjects(count=60, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=50",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 60)
        self.assertEqual(len(response.data["data"]["results"]), 50)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_and_page_size_is_less_than_10(self):
        """测试管理员查看公共课题列表，数量大于每页数量，每页数量小于10"""
        self.create_subjects(count=25, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=5",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 25)
        self.assertEqual(len(response.data["data"]["results"]), 5)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_admin_paginated_subjects_num_greater_than_page_size_and_page_size_is_exceed_max_page_size(self):
        """测试管理员查看公共课题列表，数量大于每页数量，每页数量超过最大数量"""
        self.create_subjects(count=110, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=101",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 110)
        self.assertEqual(len(response.data["data"]["results"]), 100)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion

    # region 搜索测试
    def test_public_subject_list_with_admin_search_by_title(self):
        """测试管理员查看公共课题列表，搜索课题"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?search=test_title_11",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["title"], "test_title_11")

        # 检查下一页和上一页
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_admin_search_by_title_not_exist(self):
        """测试管理员查看公共课题列表，搜索课题，课题不存在"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?search=test_title_12",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_admin_search_by_description(self):
        """测试管理员查看公共课题列表，搜索课题，搜索课题描述"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?search=test_description_11",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["description"], "test_description_11")

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    
    def test_public_subject_list_with_admin_search_by_description_not_exist(self):
        """测试管理员查看公共课题列表，搜索课题，搜索课题描述，课题不存在"""
        self.create_subjects(count=11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        response = self.client.get(
            f"{self.url}?search=test_description_12",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion
    
    # region 权限测试
    def test_public_subject_list_with_unauthorized_user(self):
        """测试未授权用户查看公共课题列表"""
        response = self.client.get(
            self.url,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_student_only_see_approved_subjects(self):
        """测试学生查看公共课题列表，只能看到已公开的课题，不能看到未公开的课题"""
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 10)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_student_search_not_approved_subjects_by_title(self):
        """测试学生查看公共课题列表，搜索未批准的课题时，能正确返回空列表"""
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        response = self.client.get(
            f"{self.url}?search=test_title_11",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_student_search_not_approved_subjects_by_description(self):
        """测试学生查看公共课题列表，搜索未批准的课题时，能正确返回空列表"""
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        response = self.client.get(
            f"{self.url}?search=test_description_11",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_teacher_can_see_public_subjects(self):
        """测试教师可以查看所有已公开的课题"""
        # 1. 自己的和其他人的已公开的课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher2_token)
            self.review_public(subject.id, token=self.admin_token)
        # 2. 自己的未公开的课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        # 3. 其他人的未公开的课题
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 22)
        self.assertEqual(len(response.data["data"]["results"]), 10)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_public_subject_list_with_teacher_search_by_title(self):
        """测试教师搜索课题时，能正确返回数据"""
        # 1. 当前教师和另外一名教师创建的已公开课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher2_token)
            self.review_public(subject.id, token=self.admin_token)
        # 2. 当前教师创建的未公开课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        # 3. 其他教师创建的未公开课题
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        
        response = self.client.get(
            f"{self.url}?search=test_title_11",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 2)
        self.assertEqual(len(response.data["data"]["results"]), 2)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_teacher_search_by_title_not_exist(self):
        """测试教师搜索课题时，课题不存在时，能正确返回空列表"""
        # 1. 当前教师和另外一名教师创建的已公开课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher2_token)
            self.review_public(subject.id, token=self.admin_token)
        # 2. 当前教师创建的未公开课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        # 3. 其他教师创建的未公开课题
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        
        response = self.client.get(
            f"{self.url}?search=test_title_12",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_public_subject_list_with_amdin_see_all_subjects(self):
        """测试管理员可以查看所有已公开的课题"""
        # 1. 当前教师和另外一名教师创建的已公开课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher_token)
            self.review_public(subject.id, token=self.admin_token)
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        for subject in Subject.objects.all():
            self.review_subjects(subject.id, "APPROVED")
            self.apply_public(subject.id, token=self.teacher2_token)
            self.review_public(subject.id, token=self.admin_token)
        # 2. 当前教师创建的未公开课题
        created_subjects = self.create_subjects(11, token=self.teacher_token)
        # 3. 其他教师创建的未公开课题
        created_subjects = self.create_subjects(11, token=self.teacher2_token)
        
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 22)
        self.assertEqual(len(response.data["data"]["results"]), 10)

        # 检查message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion

    # region 文件测试
    def test_public_subject_list_with_file(self):
        data = {
            "title": "test_title",
            "description": "test_description",
            "languages": ["C", "CPP", "JAVA", "PYTHON"],
            "description_file": SimpleUploadedFile("test.txt", content=b"test", content_type="text/plain")
        }
        response = self.client.post(
            reverse("subject-list"),
            data=data,
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        subject = Subject.objects.first()
        self.review_subjects(subject.id, "APPROVED")
        self.apply_public(subject.id, token=self.teacher_token)
        self.review_public(subject.id, token=self.admin_token)
        public_subject = PublicSubject.objects.first()
        self.assertEqual(public_subject.title, "test_title")
        self.assertEqual(public_subject.description, "test_description")
        self.assertEqual(public_subject.languages, ["C", "CPP", "JAVA", "PYTHON"])
        self.assertEqual(public_subject.creator, self.teacher)
        self.assertIsNotNone(public_subject.description_file)
        self.assertTrue(os.path.exists(public_subject.description_file.path))
        # 删除测试文件
        public_subject.delete()
        subject.delete()
    # endregion
        
