from rest_framework.test import APITestCase
from accounts.models import User
from subject.models import Subject
from django.urls import reverse
from rest_framework import status

MAX_SUBJECTS = 150

class SubjectListTestCase(APITestCase):
    """课题列表测试"""
    
    # region 测试准备用户数据
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
    
    # region 测试所有用户访问非空数据库
    def test_subject_list_with_teacher_approved_subjects(self):
        """测试教师访问时能正确返回数据列表"""
        print("-----正在测试教师访问时能正确返回数据列表-----")
        # 创建5个测试课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            self.url, 
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 5)
        self.assertEqual(len(response.data['data']['results']), 5)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时能正确返回数据列表测试结束-----") 

    def test_subject_list_with_student_approved_subjects(self):
        """测试学生访问时能正确返回数据列表"""
        print("-----正在测试学生访问时能正确返回数据列表-----")
        # 创建5个测试课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            self.url, 
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 5)
        self.assertEqual(len(response.data['data']['results']), 5)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----学生访问时能正确返回数据列表测试结束-----")

    def test_subject_list_with_admin_approved_subjects(self):
        """测试管理员访问时能正确返回数据列表"""
        print("-----正在测试管理员访问时能正确返回数据列表-----")
        # 创建5个测试课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            self.url, 
            headers={
                "Authorization": f"Bearer {self.admin_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 5) 
        self.assertEqual(len(response.data['data']['results']), 5)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----管理员访问时能正确返回数据列表测试结束-----")
    # endregion

    # region 测试所有用户访问空数据库
    def test_subject_list_with_teacher_empty_database(self):
        """测试教师访问空数据库时返回空列表"""
        print("-----正在测试教师访问空数据库时返回空列表-----")
        response = self.client.get(
            self.url, 
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问空数据库时返回空列表测试结束-----") 
    
    def test_subject_list_with_student_empty_database(self):
        """测试学生访问空数据库时返回空列表"""
        print("-----正在测试学生访问空数据库时返回空列表-----")
        response = self.client.get(
            self.url, 
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----学生访问空数据库时返回空列表测试结束-----")

    def test_subject_list_with_admin_empty_database(self):
        """测试管理员访问空数据库时返回空列表"""
        print("-----正在测试管理员访问空数据库时返回空列表-----")
        response = self.client.get(
            self.url, 
            headers={
                "Authorization": f"Bearer {self.admin_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----管理员访问空数据库时返回空列表测试结束-----")
    # endregion

    # region 测试课题列表分页
    def test_subject_list_with_teacher_paginated_subjects_num_less_or_equal_than_page_size(self):
        """测试教师访问数量小于等于每页数量时能正确分页返回数据"""
        print("-----正在测试教师访问数量小于等于每页数量时能正确分页返回数据-----")
        # 创建10个测试课题
        created_subjects = self.create_subjects(10, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            f"{self.url}?page=1&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 10)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量小于等于每页数量时能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_num_greater_than_page_size_visit_page_1(self):
        """测试教师访问数量大于每页数量时，访问第一页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问第一页时能正确分页返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            f"{self.url}?page=1&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 下一页和上一页
        self.assertIn("page=2", response.data['data']['next'])
        self.assertEqual(response.data['data']['previous'], None)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问第一页时能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_num_greater_than_page_size_and_page_is_not_int_and_page_size_is_not_int(self):
        """测试教师访问数量大于每页数量时，页码不是整数时，每页数量不是整数时显示404"""
        print("-----正在测试教师访问数量大于每页数量时，页码不是整数时，每页数量不是整数时显示404-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=a&page_size=a",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )   
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，页码不是整数时，每页数量不是整数时显示404测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_num_greater_than_page_size_and_page_size_is_not_int_and_page_is_negative(self):
        """测试教师访问数量大于每页数量时，每页数量不是整数时，页码为负数时显示404"""
        print("-----正在测试教师访问数量大于每页数量时，每页数量不是整数时，页码为负数时显示404-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            f"{self.url}?page=-1&page_size=a",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，每页数量不是整数时，页码为负数时显示404测试结束-----")
    
    def test_subject_list_with_teacher_paginated_subjects_num_greater_than_page_size_and_visit_page_2(self):
        """测试教师访问数量大于每页数量时，访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问第二页时能正确分页返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")

        response = self.client.get(
            f"{self.url}?page=2&page_size=10",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 1)  # 第二页应该只有1个课题
        # 下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        # 第一页没有page=1参数
        self.assertNotIn("page=1", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问第二页时能正确分页返回数据测试结束-----")
    
    def test_subject_list_with_teacher_paginated_subjects_num_greater_than_page_size_and_visit_last_page(self):
        """测试教师访问数量大于每页数量时，访问最后一页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问最后一页时能正确分页返回数据-----")
        # 创建25个测试课题
        created_subjects = self.create_subjects(25, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=3&page_size=10",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 25)
        self.assertEqual(len(response.data['data']['results']), 5)
        # 下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertIn("page=2", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问最后一页时能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_num_greater_than_page_size_and_visit_midlle_page(self):
        """测试教师访问数量大于每页数量时，访问中间页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问中间页时能正确分页返回数据-----")
        # 创建25个测试课题
        created_subjects = self.create_subjects(25, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=10",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 25)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 下一页和上一页
        self.assertIn("page=3", response.data['data']['next'])
        self.assertNotIn("page=1", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问中间页时能正确分页返回数据测试结束-----")
        
    def test_subject_list_with_teacher_paginated_subjects_and_visit_page_not_exist(self):
        """测试教师访问时，访问不存在的页码时能正确分页返回空列表"""
        print("-----正在测试教师访问时，访问不存在的页码时能正确分页返回空列表-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=4&page_size=10",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，访问不存在的页码时能正确分页返回空列表测试结束-----")
        
    def test_subject_list_with_teacher_paginated_subjects_and_page_size_is_bigger_than_10(self):
        """测试教师访问时，每页数量大于默认数量时能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量大于默认数量时能正确分页返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(21, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=50",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 21)
        self.assertEqual(len(response.data['data']['results']), 21)
        # 下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量大于默认数量时能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_and_page_size_is_bigger_than_10_and_visit_page_2(self):
        """测试教师访问时，每页数量大于默认数量时，访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量大于默认数量时，访问第二页时能正确分页返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(21, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=20",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 21)
        self.assertEqual(len(response.data['data']['results']), 1)
        # 下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertNotIn("page=1", response.data['data']['previous'])
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量不是默认数量时，访问第二页时能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_and_page_size_is_less_than_10(self):
        """测试教师访问时，每页数量小于默认数量时，能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量小于默认数量时，能正确分页返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=5",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 5)
        # 下一页和上一页
        self.assertIn("page=2", response.data['data']['next'])
        self.assertEqual(response.data['data']['previous'], None)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量小于默认数量时，能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_and_page_size_is_less_than_10_and_visit_page_2(self):
        """测试教师访问时，每页数量小于默认数量时，访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量小于默认数量时，访问第二页时能正确分页返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=5",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 5)
        # 下一页和上一页
        self.assertIn("page=3", response.data['data']['next'])
        self.assertNotIn("page=1", response.data['data']['previous'])
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量小于默认数量时，访问第二页时能正确分页返回数据测试结束-----")

    def test_subject_list_with_teacher_paginated_subjects_and_page_size_is_exceed_max_page_size(self):
        """测试教师访问时，每页数量大于最大数量时，显示为最大数量"""
        print("-----正在测试教师访问时，每页数量大于最大数量时，显示为最大数量-----")
        # 创建110个测试课题
        created_subjects = self.create_subjects(120, creator=self.teacher, status="APPROVED")
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=101",  # 直接拼接 URL 参数
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 120)
        self.assertEqual(len(response.data['data']['results']), 100)
        # 下一页和上一页
        self.assertIn("page=2", response.data['data']['next'])
        self.assertEqual(response.data['data']['previous'], None)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量大于最大数量时，显示为最大数量测试结束-----")
        
    # endregion

    # region 测试课题列表搜索
    def test_subject_list_with_teacher_search_by_title(self):
        """测试教师访问时，搜索课题时能正确返回数据"""
        print("-----正在测试教师访问时，搜索课题时能正确返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        # 搜索课题
        response = self.client.get(
            f"{self.url}?search=test_title_11",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['title'], "test_title_11")
        # 下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课题时能正确返回数据测试结束-----")

    def test_subject_list_with_teacher_search_by_title_not_exist(self):
        """测试教师访问时，搜索课题时，课题不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课题时，课题不存在时能正确返回空列表-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        # 搜索课题
        response = self.client.get(
            f"{self.url}?search=test_title_12",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课题时，课题不存在时能正确返回空列表测试结束-----")

    def test_subject_list_with_teacher_search_by_status(self):
        """测试教师访问时，搜索课题时，状态时能正确返回数据"""
        print("-----正在测试教师访问时，搜索课题时，状态时能正确返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")    
        # 搜索课题
        response = self.client.get(
            f"{self.url}?status=APPROVED",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课题时，状态时能正确返回数据测试结束-----")

    def test_subject_list_with_teacher_search_by_status_not_exist(self):
        """测试教师访问时，搜索课题时，状态不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课题时，状态不存在时能正确返回空列表-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        # 搜索课题
        response = self.client.get(
            f"{self.url}?status=PENDING",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )   
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课题时，状态不存在时能正确返回空列表测试结束-----")
    
    def test_subject_list_with_teacher_search_by_status_and_title(self):
        """测试教师访问时，搜索课题时，状态和课题同时存在时能正确返回数据"""
        print("-----正在测试教师访问时，搜索课题时，状态和课题同时存在时能正确返回数据-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        # 搜索课题
        response = self.client.get(
            f"{self.url}?status=APPROVED&search=test_title_11",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )   
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课题时，状态和课题同时存在时能正确返回数据测试结束-----")

    def test_subject_list_with_teacher_search_by_status_and_title_not_exist(self):
        """测试教师访问时，搜索课题时，状态和课题同时不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课题时，状态和课题同时不存在时能正确返回空列表-----")
        # 创建11个测试课题
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        # 搜索课题
        response = self.client.get(
            f"{self.url}?status=PENDING&search=test_title_12",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )   
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课题时，状态和课题同时不存在时能正确返回空列表测试结束-----")
    # endregion

    # region 测试权限
    def test_subject_list_with_unauthorized_user(self):
        """测试未授权用户访问时返回401"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_student_only_see_approved_subjects(self):
        """测试学生访问时，只能看到已批准的课题"""
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        created_subjects = self.create_subjects(11, creator=self.teacher, status="PENDING")
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 课题列表中只有已批准的课题
        for subject in response.data['data']['results']:
            self.assertEqual(subject['status'], "APPROVED")
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    
    def test_subject_list_with_student_search_not_approved_subjects_by_title(self):
        """测试学生访问时，搜索未批准的课题时，能正确返回空列表"""
        created_subjects = self.create_subjects(11, creator=self.teacher, status="PENDING")
        response = self.client.get(
            f"{self.url}?search=test_title_11",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_student_search_not_approved_subjects_by_status(self):
        """测试学生访问时，搜索未批准的课题时，能正确返回空列表"""
        created_subjects = self.create_subjects(11, creator=self.teacher, status="PENDING")
        response = self.client.get(
            f"{self.url}?status=PENDING",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_student_search_mixed_subjects_by_title(self):
        """测试学生访问时，搜索混合课题时，能正确返回数据"""
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        created_subjects = self.create_subjects(11, creator=self.teacher, status="PENDING")
        response = self.client.get(
            f"{self.url}?search=test_title_11",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_student_search_mixed_subjects_by_status(self):
        """测试学生访问时，搜索混合课题时，能正确返回数据"""
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        created_subjects = self.create_subjects(11, creator=self.teacher, status="PENDING")
        response = self.client.get(
            f"{self.url}?status=PENDING",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_student_search_mixed_subjects_by_status_and_title(self):
        """测试学生访问时，搜索混合课题时，能正确返回数据"""
        created_subjects = self.create_subjects(11, creator=self.teacher, status="APPROVED")
        created_subjects = self.create_subjects(11, creator=self.teacher, status="PENDING")
        response = self.client.get(
            f"{self.url}?status=PENDING&search=test_title_11",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_teacher_onlu_see_his_subjects_and_approved_subjects(self):
        """测试教师只能看到自己的课题和已批准的课题"""
        # 创建测试数据
        # 1. 当前教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")
        # 2. 当前教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="PENDING")
        # 3. 其他教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="APPROVED")
        # 4. 其他教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="PENDING")
        
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 应该看到：自己创建的所有课题(10个) + 其他教师创建的已批准课题(5个) = 15个
        self.assertEqual(response.data['data']['count'], 15)
        self.assertEqual(len(response.data['data']['results']), 10)  # 第一页10个
        
        # 验证结果中的课题都符合条件：要么是自己创建的，要么是已批准的
        for subject in response.data['data']['results']:
            self.assertTrue(
                subject['creator']['user_id'] == self.teacher.user_id or 
                subject['status'] == "APPROVED"
            )
        
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_subject_list_with_teacher_search_by_status_and_title(self):
        """测试教师搜索课题时，能正确返回数据"""
        # 创建测试数据
        # 1. 当前教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")
        # 2. 当前教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="PENDING")
        # 3. 其他教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="APPROVED")
        # 4. 其他教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="PENDING")
        
        response = self.client.get(
            f"{self.url}?status=APPROVED&search=test_title_1",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)
        self.assertEqual(len(response.data['data']['results']), 2)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_subject_list_with_teacher_search_by_status_and_title_not_exist(self):
        """测试教师搜索课题时，课题不存在时，能正确返回空列表"""
        # 创建测试数据
        # 1. 当前教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")
        # 2. 当前教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="PENDING")
        # 3. 其他教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="APPROVED")
        # 4. 其他教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="PENDING")
        
        response = self.client.get(
            f"{self.url}?status=APPROVED&search=test_title_12",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_subject_list_with_teacher_search_pending_subjects_only_see_his_pending_subjects(self):
        """测试教师搜索待审核课题时，只能看到自己的待审核课题"""
        # 创建测试数据
        # 1. 当前教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")
        # 2. 当前教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="PENDING")
        # 3. 其他教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="APPROVED")
        # 4. 其他教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="PENDING")
        
        response = self.client.get(
            f"{self.url}?status=PENDING",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 5)
        self.assertEqual(len(response.data['data']['results']), 5)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    
    def test_subject_list_with_admin_see_all_subjects(self):
        """测试管理员能看到所有课题"""
        # 创建测试数据
        # 1. 当前教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="APPROVED")
        # 2. 当前教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher, status="PENDING")
        # 3. 其他教师创建的已批准课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="APPROVED")
        # 4. 其他教师创建的待审核课题
        created_subjects = self.create_subjects(5, creator=self.teacher2, status="PENDING")
        
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.admin_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 20)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    # endregion
