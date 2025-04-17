from rest_framework.test import APITestCase
from rest_framework import status
from course.models import Course
from accounts.models import User
from django.urls import reverse
import datetime

MAX_COURSES = 150
class CourseUpdateTestCase(APITestCase):
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
            "min_group_size": 1
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
                "min_group_size": data["min_group_size"]
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
    def test_update_course_with_teacher(self):
        """测试教师更新课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.name, "updated_name")
        self.assertEqual(course.description, "updated_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), self.get_day(days=1))
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), self.get_day(days=2))
        self.assertNotEqual(course.updated_at, before_update_time)
        
    def test_update_course_with_student_not_joined(self):
        """测试学生更新未加入的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_update_course_with_admin(self):
        """测试管理员更新课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.name, "updated_name")
        self.assertEqual(course.description, "updated_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), self.get_day(days=1))
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), self.get_day(days=2))
        self.assertNotEqual(course.updated_at, before_update_time)

    def test_update_course_status_change_when_update_date(self):
        """测试更新课程时，课程状态的变化"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=-1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.status, "in_progress")
        
    # endregion

    # region 必填字段测试
    def test_update_course_without_name(self):
        """更新课程时，缺少必填字段name"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data["message"])
        
    def test_update_course_with_invalid_start_date(self):
        """更新课程时，start_date格式错误"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": "invalid_date",
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_date", response.data["message"])
        
    def test_update_course_with_invalid_end_date(self):
        """更新课程时，end_date格式错误"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": "invalid_date"
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.data["message"])
        
    def test_update_course_with_start_date_before_end_date(self):
        """更新课程时，start_date晚于end_date"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        before_update_time = course.updated_at
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=2),
                "end_date": self.get_day(days=1)
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("开始时间不得比结束时间迟", response.data["message"])

    # endregion

    # region 权限测试
    def test_update_course_without_login(self):
        """更新课程时，未登录用户尝试更新"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_course_with_student_update_joined_course(self):
        """更新课程时，学生更新已加入的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        self.join_course(course.course_code, token=self.student_token)
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_course_with_teacher_update_other_teacher_course(self):
        """更新课程时，教师更新其他教师的课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.teacher2_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_course_with_admin_update_course(self):
        """更新课程时，管理员更新课程"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.name, "updated_name")
        self.assertEqual(course.description, "updated_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), self.get_day(days=1))
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), self.get_day(days=2))
        
    # endregion
    
    # region 数据验证测试
    def test_update_course_with_invalid_course_id(self):
        """更新课程时，使用无效的课程ID"""
        update_data = {
            "name": "updated_name",
            "description": "updated_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.put(
            f"{self.url}invalid_id/",
            data=update_data,
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_course_with_deleted_course(self):
        """更新课程时，使用已删除的课程ID"""
        self.create_courses(1, token=self.teacher_token)
        course = Course.objects.first()
        course.delete()
        response = self.client.put(
            f"{self.url}{course.id}/",
            data={
                "name": "updated_name",
                "description": "updated_description",
                "start_date": self.get_day(days=1),
                "end_date": self.get_day(days=2)
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
    
    
    
    