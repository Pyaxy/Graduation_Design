import datetime
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User
from course.models import Course
from django.urls import reverse

MAX_COURSES = 150
class CourseJoinTestCase(APITestCase):
    """课程加入测试"""

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
        cls.url = reverse("course-join")
        
        # 准备测试课程数据
        cls.course_data_list = [{
            "name": f"test_name_{i}",
            "description": f"test_description_{i}"
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

    def create_courses(self, count=None, start_delta=1, end_delta=2):
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
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
            )
    # endregion

    # region 基础功能测试
    def test_join_course_with_student(self):
        """测试学生加入课程"""
        print("-----正在测试学生加入课程-----")
        self.create_courses(count=1)
        course_code = Course.objects.first().course_code
        response = self.client.post(
            f'{self.url}',
            data={
                "course_code": course_code
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '加入课程成功')
        self.assertEqual(response.data['data'], None)
        self.assertEqual(Course.objects.filter(students=self.student).count(), 1)
        self.assertEqual(Course.objects.filter(students=self.student).first().course_code, course_code)
        print("-----学生加入课程测试结束-----")
    # endregion

    # region 权限测试
    def test_join_course_with_teacher(self):
        """测试教师加入课程"""
        print("-----正在测试教师加入课程-----")
        self.create_courses(count=1)
        course_code = Course.objects.first().course_code
        response = self.client.post(
            f'{self.url}',
            data={
                "course_code": course_code
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], '您没有执行该操作的权限。')
        print("-----教师加入课程测试结束-----")
        
    def test_join_course_with_admin(self):
        """测试管理员加入课程"""
        print("-----正在测试管理员加入课程-----")
        self.create_courses(count=1)
        course_code = Course.objects.first().course_code
        response = self.client.post(
            f'{self.url}',
            data={
                "course_code": course_code
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], '您没有执行该操作的权限。')
        print("-----管理员加入课程测试结束-----")
    # endregion

    # region 异常测试
    def test_join_course_with_invalid_course_code(self):
        """测试加入课程时输入无效的课程码"""
        print("-----正在测试加入课程时输入无效的课程码-----")
        response = self.client.post(
            f'{self.url}',
            data={
                "course_code": "invalid_course_code"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('course_code', response.data['message'])
        print("-----加入课程时输入无效的课程码测试结束-----")

    def test_join_course_with_already_joined_course(self):
        """测试加入已经加入的课程"""
        print("-----正在测试加入已经加入的课程-----")
        self.create_courses(count=1)
        course_code = Course.objects.first().course_code
        response = self.client.post(
            f'{self.url}',
            data={
                "course_code": course_code
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(
            f'{self.url}',
            data={
                "course_code": course_code
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('您已经加入该课程', response.data['message'])
        print("-----加入已经加入的课程测试结束-----")
    # endregion