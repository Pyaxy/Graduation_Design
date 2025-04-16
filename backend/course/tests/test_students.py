from rest_framework.test import APITestCase
from rest_framework import status
from course.models import Course
from accounts.models import User
from django.urls import reverse
import datetime

MAX_STUDENTS = 150
MAX_COURSES = 150
class CourseStudentsTestCase(APITestCase):

    # region 测试数据准备
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
        cls.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
            user_id="admin001",
            name="admin",
            school="admin school",
            role="ADMIN"
        )
        cls.student = User.objects.create_user(
            email="student@example.com",
            password="student123",
            user_id="student000",
            name="student",
            school="student school",
            role="STUDENT"
        )
        cls.students = [
            User.objects.create_user(
                email=f"student{i}@example.com",
                password="student123",
                user_id=f"student00{i}",
                name=f"student{i}",
                school="student school",
                role="STUDENT"
            )
            for i in range(1, MAX_STUDENTS + 1)
        ]
        cls.url = reverse("course-list")
        cls.course_data_list = [
            {
                "name": f"test_course_{i}",
                "description": f"test_description_{i}",
            }
            for i in range(1, MAX_COURSES + 1)
        ]
        print("-----测试数据准备完成-----\n")

    def setUp(self):
        """每个测试方法执行前的准备工作"""
        # 清空数据库
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
        self.admin_token = self.client.post(
            reverse("login"),
            {"email": self.admin.email, "password": "admin123"}
        ).data["data"]["access"]
        self.student_token = self.client.post(
            reverse("login"),
            {"email": self.student.email, "password": "student123"}
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
                "end_date": self.get_day(days=end_delta)
                },
                HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
            )

    def join_course(self, course_code, token=None):
        """加入课程"""
        return self.client.post(
            reverse("course-join"),
            data={
                "course_code": course_code
            },
            headers={"Authorization": f"Bearer {token if token else self.student_token}"}
        )

    def bulk_join_course(self, course_code, count):
        """批量加入课程"""
        students = self.students[:count]
        for student in students:
            access = self.client.post(
                reverse("login"),
                data={
                    "email": student.email,
                    "password": "student123"
                },
            ).data["data"]["access"]
            response = self.join_course(course_code, token=access)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    # endregion

    # region 基础功能测试
    def test_list_students_with_teacher(self):
        """教师可以查看课程的学生列表"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 10)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 10)
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)
        self.assertEqual(len(response.data["data"]["results"]), 10)
        for student in response.data["data"]["results"]:
            self.assertIn(student["user_id"], [student.user_id for student in self.students[:10]])

    def test_list_students_with_student(self):
        """学生可以查看自己的课程学生列表"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.join_course(course.course_code, token=self.student_token)
        self.bulk_join_course(course.course_code, 9)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 10)
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)
        self.assertEqual(len(response.data["data"]["results"]), 10)
        for student in response.data["data"]["results"]:
            self.assertIn(student["user_id"], [student.user_id for student in course.students.all()])

    def test_list_students_with_admin(self):
        """管理员可以查看所有课程的学生列表"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 10)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 10)
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)
        self.assertEqual(len(response.data["data"]["results"]), 10)
        for student in response.data["data"]["results"]:
            self.assertIn(student["user_id"], [student.user_id for student in self.students[:10]])

    # endregion

    # region 测试用户访问空数据库
    def test_list_students_with_teacher_empty_database(self):
        """测试教师访问空数据库时返回空列表"""
        print("-----正在测试教师访问空数据库时返回空列表-----")
        response = self.client.get(
            f"{self.url}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----教师访问空数据库时返回空列表测试结束-----")

    def test_list_students_with_student_empty_database(self):
        """测试学生访问空数据库时返回空列表"""
        print("-----正在测试学生访问空数据库时返回空列表-----")
        response = self.client.get(
            f"{self.url}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----学生访问空数据库时返回空列表测试结束-----")

    def test_list_students_with_admin_empty_database(self):
        """测试管理员访问空数据库时返回空列表"""
        print("-----正在测试管理员访问空数据库时返回空列表-----")
        response = self.client.get(
            f"{self.url}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----管理员访问空数据库时返回空列表测试结束-----")
    def test_list_students_with_teacher_course_have_no_students(self):
        """测试教师访问课程没有学生时返回空列表"""
        print("-----正在测试教师访问课程没有学生时返回空列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        print("-----教师访问课程没有学生时返回空列表测试结束-----")

    def test_list_students_with_admin_course_have_no_students(self):
        """测试管理员访问课程没有学生时返回空列表"""
        print("-----正在测试管理员访问课程没有学生时返回空列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        print("-----管理员访问课程没有学生时返回空列表测试结束-----")
        
    # endregion

    # region 测试分页功能
    def test_list_students_with_teacher_paginated_students_num_less_or_equal_than_page_size(self):
        """测试教师访问数量小于等于每页数量时能正确分页返回数据"""
        print("-----正在测试教师访问数量小于等于每页数量时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 10)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 10)
        self.assertEqual(len(response.data["data"]["results"]), 10)
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)
        print("-----教师访问数量小于等于每页数量时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_visit_page_1(self):
        """测试教师访问数量大于每页数量时,访问第一页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,访问第一页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 10)
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)
        print("-----教师访问数量大于每页数量时,访问第一页时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_page_is_not_int_and_page_size_is_not_int(self):
        """测试教师访问数量大于每页数量时,页码不是整数时,每页数量不是整数时显示404"""
        print("-----正在测试教师访问数量大于每页数量时,页码不是整数时,每页数量不是整数时显示404-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=a&page_size=a",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----教师访问数量大于每页数量时,页码不是整数时,每页数量不是整数时显示404测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_page_size_is_not_int_and_page_is_negative(self):
        """测试教师访问数量大于每页数量时,每页数量不是整数时,页码为负数时显示404"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量不是整数时,页码为负数时显示404-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=-1&page_size=a",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----教师访问数量大于每页数量时,每页数量不是整数时,页码为负数时显示404测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_visit_page_2(self):
        """测试教师访问数量大于每页数量时,访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,访问第二页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=2&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertNotIn("page=1", response.data["data"]["previous"])
        self.assertEqual(response.data["data"]["next"], None)
        print("-----教师访问数量大于每页数量时,访问第二页时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_visit_last_page(self):
        """测试教师访问数量大于每页数量时,访问最后一页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,访问最后一页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 25)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=3&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 25)
        self.assertEqual(len(response.data["data"]["results"]), 5)
        self.assertIn("page=2", response.data["data"]["previous"])
        self.assertEqual(response.data["data"]["next"], None)
        print("-----教师访问数量大于每页数量时,访问最后一页时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_visit_middle_page(self):
        """测试教师访问数量大于每页数量时,访问中间页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,访问中间页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 25)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=2&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 25)
        self.assertEqual(len(response.data["data"]["results"]), 10)
        self.assertNotIn("page=1", response.data["data"]["previous"])
        self.assertIn("page=3", response.data["data"]["next"])
        print("-----教师访问数量大于每页数量时,访问中间页时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_and_visit_page_not_exist(self):
        """测试教师访问数量大于每页数量时,访问不存在的页码时显示404"""
        print("-----正在测试教师访问数量大于每页数量时,访问不存在的页码时显示404-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=4&page_size=10",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----教师访问数量大于每页数量时,访问不存在的页码时显示404测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_page_size_is_bigger_than_10(self):
        """测试教师访问数量大于每页数量时,每页数量大于默认数量时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量大于默认数量时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 21)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=50",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 21)
        self.assertEqual(len(response.data["data"]["results"]), 21)
        self.assertEqual(response.data["data"]["next"], None)
        self.assertEqual(response.data["data"]["previous"], None)
        print("-----教师访问数量大于每页数量时,每页数量大于默认数量时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_num_greater_than_page_size_and_page_size_is_bigger_than_10_and_visit_page_2(self):
        """测试教师访问数量大于每页数量时,每页数量大于默认数量时,访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量大于默认数量时,访问第二页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 21)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=2&page_size=20",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 21)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertNotIn("page=1", response.data["data"]["previous"])
        self.assertEqual(response.data["data"]["next"], None)
        print("-----教师访问数量大于每页数量时,每页数量大于默认数量时,访问第二页时能正确分页返回数据测试结束-----")
        
    def test_list_students_with_teacher_paginated_students_and_page_size_is_less_than_10(self):
        """测试教师访问数量大于每页数量时,每页数量小于默认数量时,能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量小于默认数量时,能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=5",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 5)
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)
        print("-----教师访问数量大于每页数量时,每页数量小于默认数量时,能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_and_page_size_is_less_than_10_and_visit_page_2(self):
        """测试教师访问数量大于每页数量时,每页数量小于默认数量时,访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量小于默认数量时,访问第二页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=2&page_size=5",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 11)
        self.assertEqual(len(response.data["data"]["results"]), 5)
        self.assertNotIn("page=1", response.data["data"]["previous"])
        self.assertIn("page=3", response.data["data"]["next"])
        print("-----教师访问数量大于每页数量时,每页数量小于默认数量时,访问第二页时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_paginated_students_and_page_size_is_exceed_max_page_size(self):
        """测试教师访问数量大于每页数量时,每页数量大于最大数量时,显示为最大数量"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量大于最大数量时,显示为最大数量-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 120)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=101",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 120)
        self.assertEqual(len(response.data["data"]["results"]), 100)
        self.assertIn("page=2", response.data["data"]["next"])
        self.assertEqual(response.data["data"]["previous"], None)
        print("-----教师访问数量大于每页数量时,每页数量大于最大数量时,显示为最大数量测试结束-----")

    def test_list_students_with_teacher_paginated_students_and_page_size_is_exceed_max_page_size_and_visit_page_2(self):
        """测试教师访问数量大于每页数量时,每页数量大于最大数量时,访问第二页时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,每页数量大于最大数量时,访问第二页时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 120)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=2&page_size=100",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 120)
        self.assertEqual(len(response.data["data"]["results"]), 20)
        self.assertNotIn("page=1", response.data["data"]["previous"])
        self.assertEqual(response.data["data"]["next"], None)
        print("-----教师访问数量大于每页数量时,每页数量大于最大数量时,访问第二页时能正确分页返回数据测试结束-----")

    # endregion

    # region 测试搜索功能
    def test_list_students_with_teacher_search_by_name(self):
        """测试教师访问数量大于每页数量时,搜索学生时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,搜索学生时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student11",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["name"], "student11")
        print("-----教师访问数量大于每页数量时,搜索学生时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_search_by_name_not_exist(self):
        """测试教师访问数量大于每页数量时,搜索学生时,学生不存在时能正确返回空列表"""
        print("-----正在测试教师访问数量大于每页数量时,搜索学生时,学生不存在时能正确返回空列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student12",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)
        print("-----教师访问数量大于每页数量时,搜索学生时,学生不存在时能正确返回空列表测试结束-----")

    def test_list_students_with_teacher_search_by_user_id(self):
        """测试教师访问数量大于每页数量时,搜索学生时,用户id时能正确分页返回数据"""
        print("-----正在测试教师访问数量大于每页数量时,搜索学生时,用户id时能正确分页返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student0011",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["user_id"], "student0011")
        print("-----教师访问数量大于每页数量时,搜索学生时,用户id时能正确分页返回数据测试结束-----")

    def test_list_students_with_teacher_search_by_user_id_not_exist(self):
        """测试教师访问数量大于每页数量时,搜索学生时,用户id不存在时能正确返回空列表"""
        print("-----正在测试教师访问数量大于每页数量时,搜索学生时,用户id不存在时能正确返回空列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student0012",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)
        print("-----教师访问数量大于每页数量时,搜索学生时,用户id不存在时能正确返回空列表测试结束-----")
    # endregion

    # region 测试权限
    def test_list_students_with_unauthorized_user(self):
        """测试未授权用户访问时返回401"""
        print("-----正在测试未授权用户访问时返回401-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/students/",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print("-----测试未授权用户访问时返回401测试结束-----")

    def test_list_students_with_student_only_can_see_joined_courses_students(self):
        """测试学生访问时,只能看到已加入的课程的学生"""
        print("-----正在测试学生访问时,只能看到已加入的课程的学生-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        self.join_course(course.course_code, self.student_token)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_students_with_student_can_not_see_not_joined_courses_students(self):
        """测试学生访问时,不能看到未加入的课程的学生"""
        print("-----正在测试学生访问时,不能看到未加入的课程的学生-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----测试学生访问时,不能看到未加入的课程的学生测试结束-----")

    def test_list_students_with_student_can_not_see_not_joined_courses_students_by_name(self):
        """测试学生访问时,不能看到未加入的课程的学生,搜索时能正确返回空列表"""
        print("-----正在测试学生访问时,不能看到未加入的课程的学生,搜索时能正确返回空列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student11",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----测试学生访问时,不能看到未加入的课程的学生,搜索时能正确返回空列表测试结束-----")

    def test_list_students_with_teacher_can_see_his_courses_students(self):
        """测试教师访问时,可以查看自己创建的课程的学生列表"""
        print("-----正在测试教师访问时,可以查看自己创建的课程的学生列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("-----测试教师访问时,可以查看自己创建的课程的学生列表测试结束-----")

    def test_list_students_with_teacher_can_see_his_courses_students_by_name(self):
        """测试教师访问时,可以查看自己创建的课程的学生列表,搜索时能正确返回数据"""
        print("-----正在测试教师访问时,可以查看自己创建的课程的学生列表,搜索时能正确返回数据-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student11",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["name"], "student11")
        print("-----测试教师访问时,可以查看自己创建的课程的学生列表,搜索时能正确返回数据测试结束-----")

    def test_list_students_with_teacher_can_not_see_other_teachers_courses_students(self):
        """测试教师访问时,不能查看其他教师创建的课程的学生列表"""
        print("-----正在测试教师访问时,不能查看其他教师创建的课程的学生列表-----")
        self.create_courses(1, token=self.teacher2_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----测试教师访问时,不能查看其他教师创建的课程的学生列表测试结束-----")

    def test_list_students_with_teacher_can_not_see_other_teachers_courses_students_by_name(self):
        """测试教师访问时,不能查看其他教师创建的课程的学生列表,搜索时能正确返回空列表"""
        print("-----正在测试教师访问时,不能查看其他教师创建的课程的学生列表,搜索时能正确返回空列表-----")
        self.create_courses(1, token=self.teacher2_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/?page=1&page_size=10&student_search=student11",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("-----测试教师访问时,不能查看其他教师创建的课程的学生列表,搜索时能正确返回空列表测试结束-----")

    def test_list_students_with_admin_can_see_all_students(self):
        """测试管理员访问时,可以查看所有课程的学生列表"""
        print("-----正在测试管理员访问时,可以查看所有课程的学生列表-----")
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.bulk_join_course(course.course_code, 11)
        response = self.client.get(
            f"{self.url}{course.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.delete()
        self.create_courses(1, token=self.teacher2_token)
        course2 = Course.objects.first()
        self.bulk_join_course(course2.course_code, 11)
        response = self.client.get(
            f"{self.url}{course2.id}/students/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("-----测试管理员访问时,可以查看所有课程的学生列表测试结束-----")
        

    # endregion

