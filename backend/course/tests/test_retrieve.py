from rest_framework.test import APITestCase
from course.models import Course
from accounts.models import User
from django.urls import reverse
from rest_framework import status
import datetime

MAX_COURSES = 150
class CourseRetrieveTestCase(APITestCase):
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
        cls.student2 = User.objects.create_user(
            email="student2@example.com",
            password="student123",
            user_id="student002",
            name="student2",
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

        self.student2_token = self.client.post(
            reverse("login"),
            {"email": self.student2.email, "password": "student123"}
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
    def join_course(self, course_code, token=None):
        """加入课程"""
        self.client.post(
            reverse("course-join"),
            data={
                "course_code": course_code
            },
            headers={"Authorization": f"Bearer {token if token else self.student_token}"}
        )
    # endregion

    # region 基础功能测试
    def test_retrieve_with_teacher(self):
        """教师可以查看自己的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], course.name)
        self.assertEqual(response.data["data"]["description"], course.description)
        self.assertEqual(response.data["data"]["start_date"], course.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["end_date"], course.end_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["status"], course.status)
        self.assertEqual(len(response.data["data"]["students"]), 0)
        self.assertEqual(response.data["data"]["teacher"]["user_id"], self.teacher.user_id)
        self.assertEqual(response.data["data"]["teacher"]["name"], self.teacher.name)
        self.assertEqual(response.data["data"]["teacher"]["role"], self.teacher.role)
        self.assertEqual(response.data["data"]["course_code"], course.course_code)
        
    def test_retrieve_with_student(self):
        """学生可以查看自己的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.join_course(course.course_code, token=self.student_token)
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], course.name)
        self.assertEqual(response.data["data"]["description"], course.description)
        self.assertEqual(response.data["data"]["start_date"], course.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["end_date"], course.end_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["status"], course.status)
        self.assertEqual(len(response.data["data"]["students"]), 1)
        self.assertEqual(response.data["data"]["students"][0]["user_id"], self.student.user_id)
        self.assertEqual(response.data["data"]["students"][0]["name"], self.student.name)
        self.assertEqual(response.data["data"]["students"][0]["role"], self.student.role)
        self.assertEqual(response.data["data"]["teacher"]["user_id"], self.teacher.user_id)
        self.assertEqual(response.data["data"]["teacher"]["name"], self.teacher.name)
        self.assertEqual(response.data["data"]["teacher"]["role"], self.teacher.role)
        self.assertEqual(response.data["data"]["course_code"], course.course_code)
        
    def test_retrieve_with_admin(self):
        """管理员可以查看所有课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], course.name)
        self.assertEqual(response.data["data"]["description"], course.description)
        self.assertEqual(response.data["data"]["start_date"], course.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["end_date"], course.end_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["status"], course.status)
        self.assertEqual(len(response.data["data"]["students"]), 0)
        self.assertEqual(response.data["data"]["teacher"]["user_id"], self.teacher.user_id)
        self.assertEqual(response.data["data"]["teacher"]["name"], self.teacher.name)
        self.assertEqual(response.data["data"]["teacher"]["role"], self.teacher.role)
        self.assertEqual(response.data["data"]["course_code"], course.course_code)
    # endregion

    # region 权限测试
    def test_retrieve_with_unlogin_user(self):
        """未登录用户不能查看课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_with_student_not_joined(self):
        """学生不能查看未加入的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_with_teacher_and_course_is_his_course(self):
        """教师可以查看自己的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], course.name)
        self.assertEqual(response.data["data"]["description"], course.description)
        self.assertEqual(response.data["data"]["start_date"], course.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["end_date"], course.end_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["status"], course.status)
        self.assertEqual(len(response.data["data"]["students"]), 0)
        self.assertEqual(response.data["data"]["teacher"]["user_id"], self.teacher.user_id)
        self.assertEqual(response.data["data"]["teacher"]["name"], self.teacher.name)
        self.assertEqual(response.data["data"]["teacher"]["role"], self.teacher.role)
        self.assertEqual(response.data["data"]["course_code"], course.course_code)

    def test_retrieve_with_teacher_and_course_is_not_his_course(self):
        """教师不能查看其他教师的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_with_admin_and_course_is_his_course(self):
        """管理员可以查看所有课程"""
        self.create_courses(1, token=self.teacher_token)
        self.create_courses(1, token=self.teacher2_token)
        for course in Course.objects.all():
            response = self.client.get(
                f"{self.url}{course.id}/",
                HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    # endregion

    # region 数据完整性测试
    def test_retrieve_with_many_students(self):
        """查看存在多个学生的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        
        
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], str(course.id))
        self.assertEqual(response.data["data"]["name"], course.name)
        self.assertEqual(response.data["data"]["description"], course.description)
        self.assertEqual(response.data["data"]["teacher"]["user_id"], self.teacher.user_id)
        self.assertEqual(response.data["data"]["teacher"]["name"], self.teacher.name)
        self.assertEqual(response.data["data"]["teacher"]["role"], self.teacher.role)
        self.assertEqual(response.data["data"]["start_date"], course.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["end_date"], course.end_date.strftime("%Y-%m-%d"))
        self.assertEqual(response.data["data"]["status"], course.status)
        self.assertEqual(len(response.data["data"]["students"]), 2)
        self.assertEqual(response.data["data"]["students"][0]["user_id"], self.student.user_id)
        self.assertEqual(response.data["data"]["students"][1]["user_id"], self.student2.user_id)
        self.assertEqual(response.data["data"]["course_code"], course.course_code)
    # endregion

    # region 异常情况测试
    def test_retrieve_with_nonexistent_course_id(self):
        """查看不存在id的课程"""
        response = self.client.get(
            f"{self.url}999999/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_with_deleted_course(self):
        """查看已删除的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        course.delete()
        response = self.client.get(
            f"{self.url}{course.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_with_invalid_course_id(self):
        """查看无效的课程id"""
        response = self.client.get(
            f"{self.url}invalid_id/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
