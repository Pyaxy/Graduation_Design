import datetime
from rest_framework.test import APITestCase
from accounts.models import User
from course.models import Course
from django.urls import reverse
from rest_framework import status

MAX_COURSES = 150

class CourseListTestCase(APITestCase):
    """课程列表测试"""

    # region 测试准备用户数据
    @classmethod
    def setUpTestData(cls):
        """类级别的测试数据准备，只执行一次"""
        print("\n-----开始准备测试数据-----")
        
        # 清空数据库
        Course.objects.all().delete()
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
        cls.url = reverse("course-list")
        
        # 准备测试课程数据
        cls.course_data_list = [{
            "name": f"test_name_{i}",
            "description": f"test_description_{i}",
            "max_group_size": 3,
            "min_group_size": 1,
            "max_subject_selections": 1
        } for i in range(1, MAX_COURSES + 1)]
        
        print("-----测试数据准备完成-----\n")

    def setUp(self):
        """每个测试方法执行前的准备工作"""
        # 清空课程数据，保持数据库干净
        Course.objects.all().delete()
        
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

    def get_day(self, days, format="%Y-%m-%d"):
        """获取当前日期的前/后days天的日期"""
        today = datetime.datetime.now()
        return (today + datetime.timedelta(days=days)).strftime(format)

    def create_courses(self, count=None, start_delta=1, end_delta=2, token=None):
        """批量创建测试课程"""
        data_to_create = self.course_data_list[:count] if count else self.course_data_list
        for data in data_to_create:
            self.client.post(
                reverse("course-list"),
                data={
                "name": data["name"],
                "description": data["description"],
                "start_date": self.get_day(days=start_delta),
                "end_date": self.get_day(days=end_delta),
                "max_group_size": data["max_group_size"],
                "min_group_size": data["min_group_size"],
                "max_subject_selections": data["max_subject_selections"]
                },
                HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
            )
    # endregion
    
    # region 测试所有用户访问非空数据库
    def test_course_list_with_teacher(self):
        """测试教师访问时能正确返回数据列表"""
        self.create_courses(count=10, token=self.teacher_token)
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 10)
        self.assertEqual(len(response.data['data']['results']), 10)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时能正确返回数据列表测试结束-----") 

    def test_course_list_with_student(self):
        """测试学生访问时能正确返回数据列表"""
        self.create_courses(count=1, token=self.teacher_token)
        # 加入课程
        course_code = Course.objects.first().course_code
        response = self.client.post(
            reverse("course-join"),
            data={
                "course_code": course_code
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 访问课程列表
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        # 检查返回数据
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----学生访问时能正确返回数据列表测试结束-----") 

    def test_course_list_with_admin(self):
        """测试管理员访问时能正确返回数据列表"""
        self.create_courses(count=10, token=self.teacher_token)
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.admin_token}"
            }
        )
        # 检查返回数据
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 10)
        self.assertEqual(len(response.data['data']['results']), 10)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----管理员访问时能正确返回数据列表测试结束-----") 
    # endregion

    # region 测试所有用户访问空数据库
    def test_course_list_with_teacher_empty_database(self):
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

    def test_course_list_with_student_empty_database(self):
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

    def test_course_list_with_admin_empty_database(self):
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

    # region 测试分页功能
    def test_course_list_with_teacher_paginated_courses_num_less_or_equal_than_page_size(self):
        """测试教师访问数量小于等于每页数量时能正确分页返回数据"""
        print("-----正在测试教师访问数量小于等于每页数量时能正确分页返回数据-----")
        # 创建10个测试课程
        created_courses = self.create_courses(10, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 10)
        self.assertEqual(len(response.data['data']['results']), 10)

        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量小于等于每页数量时能正确分页返回数据测试结束-----")

    def test_course_list_with_teacher_paginated_courses_num_greater_than_page_size_visit_page_1(self):
        """测试教师访问数量大于每页数量时，访问第一页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问第一页时能正确分页返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 10)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data['data']['next'])
        self.assertEqual(response.data['data']['previous'], None)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问第一页时能正确分页返回数据测试结束-----")

    def test_course_list_with_teacher_paginated_courses_num_greater_than_page_size_and_page_is_not_int_and_page_size_is_not_int(self):
        """测试教师访问数量大于每页数量时，页码不是整数时，每页数量不是整数时显示404"""
        print("-----正在测试教师访问数量大于每页数量时，页码不是整数时，每页数量不是整数时显示404-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
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
        
    def test_course_list_with_teacher_paginated_courses_num_greater_than_page_size_and_page_size_is_not_int_and_page_is_negative(self):
        """测试教师访问数量大于每页数量时，每页数量不是整数时，页码为负数时显示404"""
        print("-----正在测试教师访问数量大于每页数量时，每页数量不是整数时，页码为负数时显示404-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
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
        
    def test_course_list_with_teacher_paginated_courses_num_greater_than_page_size_and_visit_page_2(self):
        """测试教师访问数量大于每页数量时，访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问第二页时能正确分页返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 1)

        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertNotIn("page=1", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问第二页时能正确分页返回数据测试结束-----")

    def test_course_list_with_teacher_paginated_courses_num_greater_than_page_size_and_visit_last_page(self):
        """测试教师访问数量大于每页数量时，访问最后一页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问最后一页时能正确分页返回数据-----")
        # 创建25个测试课程
        created_courses = self.create_courses(25, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=3&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 25)
        self.assertEqual(len(response.data['data']['results']), 5)

        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertIn("page=2", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问最后一页时能正确分页返回数据测试结束-----")

    def test_course_list_with_teacher_paginated_courses_num_greater_than_page_size_and_visit_midlle_page(self):
        """测试教师访问数量大于每页数量时，访问中间页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时，访问中间页时能正确分页返回数据-----")
        # 创建25个测试课程
        created_courses = self.create_courses(25, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 25)
        self.assertEqual(len(response.data['data']['results']), 10)

        # 检查下一页和上一页
        self.assertIn("page=3", response.data['data']['next'])
        self.assertNotIn("page=1", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问数量大于每页数量时，访问中间页时能正确分页返回数据测试结束-----")

    def test_course_list_with_teacher_paginated_courses_and_visit_page_not_exist(self):
        """测试教师访问时，访问不存在的页码时能正确分页返回空列表"""
        print("-----正在测试教师访问时，访问不存在的页码时能正确分页返回空列表-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=4&page_size=10",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，访问不存在的页码时能正确分页返回空列表测试结束-----")
    
    def test_course_list_with_teacher_paginated_courses_and_page_size_is_bigger_than_10(self):
        """测试教师访问时，每页数量大于默认数量时能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量大于默认数量时能正确分页返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(21, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=50",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 21)
        self.assertEqual(len(response.data['data']['results']), 21)

        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)
        
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量大于默认数量时能正确分页返回数据测试结束-----")
        
    def test_course_list_with_teacher_paginated_courses_and_page_size_is_bigger_than_10_and_visit_page_2(self):
        """测试教师访问时，每页数量大于默认数量时，访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量大于默认数量时，访问第二页时能正确分页返回数据-----")
        # 创建21个测试课程
        created_courses = self.create_courses(21, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=20",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 21)
        self.assertEqual(len(response.data['data']['results']), 1)

        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertNotIn("page=1", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量大于默认数量时，访问第二页时能正确分页返回数据测试结束-----")
        
    def test_course_list_with_teacher_paginated_courses_and_page_size_is_less_than_10(self):
        """测试教师访问时，每页数量小于默认数量时，能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量小于默认数量时，能正确分页返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=5",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 5)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data['data']['next'])
        self.assertEqual(response.data['data']['previous'], None)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量小于默认数量时，能正确分页返回数据测试结束-----")

    def test_course_list_with_teacher_paginated_courses_and_page_size_is_less_than_10_and_visit_page_2(self):
        """测试教师访问时，每页数量小于默认数量时，访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问时，每页数量小于默认数量时，访问第二页时能正确分页返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=2&page_size=5",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 11)
        self.assertEqual(len(response.data['data']['results']), 5)

        # 检查下一页和上一页
        self.assertIn("page=3", response.data['data']['next'])
        self.assertNotIn("page=1", response.data['data']['previous'])

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量小于默认数量时，访问第二页时能正确分页返回数据测试结束-----")
        
    def test_course_list_with_teacher_paginated_courses_and_page_size_is_exceed_max_page_size(self):
        """测试教师访问时，每页数量大于最大数量时，显示为最大数量"""
        print("-----正在测试教师访问时，每页数量大于最大数量时，显示为最大数量-----")
        # 创建110个测试课程
        created_courses = self.create_courses(120, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?page=1&page_size=101",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 120)
        self.assertEqual(len(response.data['data']['results']), 100)

        # 检查下一页和上一页
        self.assertIn("page=2", response.data['data']['next'])
        self.assertEqual(response.data['data']['previous'], None)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，每页数量大于最大数量时，显示为最大数量测试结束-----")
        
    # endregion

    # region 测试搜索功能
    def test_course_list_with_teacher_search_by_name(self):
        """测试教师访问时，搜索课程时能正确返回数据"""
        print("-----正在测试教师访问时，搜索课程时能正确返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?search=test_name_11",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['name'], "test_name_11")
        
        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)
        
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课程时能正确返回数据测试结束-----")

    def test_course_list_with_teacher_search_by_name_not_exist(self):
        """测试教师访问时，搜索课程时，课程不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课程时，课程不存在时能正确返回空列表-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?search=test_name_12",
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
        print("-----教师访问时，搜索课程时，课程不存在时能正确返回空列表测试结束-----")
        
    def test_course_list_with_teacher_search_by_status(self):
        """测试教师访问时，搜索课程时，状态时能正确返回数据"""
        print("-----正在测试教师访问时，搜索课程时，状态时能正确返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?status=not_started",
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
        print("-----教师访问时，搜索课程时，状态时能正确返回数据测试结束-----")

    def test_course_list_with_teacher_search_by_status_not_exist(self):
        """测试教师访问时，搜索课程时，状态不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课程时，状态不存在时能正确返回空列表-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?status=completed",
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
        print("-----教师访问时，搜索课程时，状态不存在时能正确返回空列表测试结束-----")
        
    def test_course_list_with_teacher_search_by_status_and_name(self):
        """测试教师访问时，搜索课程时，状态和名称同时存在时能正确返回数据"""
        print("-----正在测试教师访问时，搜索课程时，状态和名称同时存在时能正确返回数据-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?status=not_started&search=test_name_11",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['name'], "test_name_11")
        
        # 检查下一页和上一页
        self.assertEqual(response.data['data']['next'], None)
        self.assertEqual(response.data['data']['previous'], None)
        
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课程时，状态和名称同时存在时能正确返回数据测试结束-----")
        
    def test_course_list_with_teacher_search_by_status_and_name_not_exist(self):
        """测试教师访问时，搜索课程时，状态存在和名称不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课程时，状态存在和名称不存在时能正确返回空列表-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?status=not_started&search=test_name_12",
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
        print("-----教师访问时，搜索课程时，状态和名称同时不存在时能正确返回空列表测试结束-----")
        
    def test_course_list_with_teacher_search_by_status_and_name_not_exist(self):
        """测试教师访问时，搜索课程时，状态和名称同时不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课程时，状态和名称同时不存在时能正确返回空列表-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?status=completed&search=test_name_12",
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
        print("-----教师访问时，搜索课程时，状态和名称同时不存在时能正确返回空列表测试结束-----")
    
    def test_course_list_with_teacher_search_by_invalid_status(self):
        """测试教师访问时，搜索课程时，状态不存在时能正确返回空列表"""
        print("-----正在测试教师访问时，搜索课程时，状态不存在时能正确返回空列表-----")
        # 创建11个测试课程
        created_courses = self.create_courses(11, token=self.teacher_token)
        
        response = self.client.get(
            f"{self.url}?status=not_exist",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        print("-----教师访问时，搜索课程时，状态不存在时能正确返回空列表测试结束-----")
        
    # endregion

    # region 测试权限
    def test_course_list_with_unauthorized_user(self):
        """测试未授权用户访问时返回401"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_course_list_with_student_only_see_joined_courses(self):
        """测试学生访问时，只能看到已加入的课程"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        course_code = Course.objects.first().course_code
        response = self.client.post(
            reverse("course-join"),
            data={
                "course_code": course_code
            },
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['course_code'], course_code)

    def test_course_list_with_student_can_not_see_not_joined_courses(self):
        """测试学生访问时，不能看到未加入的课程"""
        created_courses = self.create_courses(11, token=self.teacher_token)
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

    def test_course_list_with_student_search_not_joined_courses_by_name(self):
        """测试学生访问时，搜索课程未加入时，能正确返回空列表"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        response = self.client.get(
            f"{self.url}?search=test_name_5",
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

    def test_course_list_with_student_search_not_joined_courses_by_status(self):
        """测试学生访问时，搜索课程未加入时，能正确返回空列表"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        response = self.client.get(
            f"{self.url}?status=not_started",
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


    def test_course_list_with_student_search_joined_courses_by_name(self):
        """测试学生访问时，搜索课程已加入时，能正确返回数据"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        course_code = Course.objects.first().course_code
        name = Course.objects.first().name
        response = self.client.post(
            reverse("course-join"),
            data={
                "course_code": course_code
            },
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(
            f"{self.url}?search={name}",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['name'], name)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_course_list_with_student_search_joined_courses_by_status(self):
        """测试学生访问时，搜索课程已加入时，能正确返回数据"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        course_code = Course.objects.first().course_code
        status_ = Course.objects.first().status
        response = self.client.post(
            reverse("course-join"),
            data={
                "course_code": course_code
            },
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(
            f"{self.url}?status={status_}",
            headers={
                "Authorization": f"Bearer {self.student_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['status'], status_)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_course_list_with_teadcher_only_see_his_courses(self):
        """测试教师访问时，只能看到自己的课程"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        created_courses = self.create_courses(11, token=self.teacher2_token)
        response = self.client.get(
            self.url,
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

    def test_course_list_with_teacher_search_by_status_and_name(self):
        """测试教师访问时，搜索课程时，状态和名称同时存在时能正确返回数据"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        course_code = Course.objects.first().course_code
        name = Course.objects.first().name
        status_ = Course.objects.first().status
        response = self.client.get(
            f"{self.url}?status={status_}&search={name}",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['name'], name)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_course_list_with_teacher_search_by_status_and_name_not_exist(self):
        """测试教师访问时，搜索课程时，状态和名称同时不存在时能正确返回空列表"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        response = self.client.get(
            f"{self.url}?status=completed&search=test_name_12",
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

    def test_course_list_with_teacher_search_by_status_and_name_not_exist(self):
        """测试教师访问时，搜索课程时，只能看到自己的课程"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        name1 = Course.objects.first().name
        created_courses = self.create_courses(11, token=self.teacher2_token)
        name2 = Course.objects.first().name
        response = self.client.get(
            f"{self.url}?search={name1}",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['name'], name1)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        response = self.client.get(
            f"{self.url}?search={name2}",
            headers={
                "Authorization": f"Bearer {self.teacher_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['name'], name2)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_admin_see_all_courses(self):
        """测试管理员能看到所有课程"""
        created_courses = self.create_courses(11, token=self.teacher_token)
        created_courses = self.create_courses(11, token=self.teacher2_token)
        response = self.client.get(
            self.url,
            headers={
                "Authorization": f"Bearer {self.admin_token}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 22)
        self.assertEqual(len(response.data['data']['results']), 10)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    # endregion
        