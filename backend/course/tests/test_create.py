import datetime
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from course.models import Course
from accounts.models import User

class CourseCreateTestCase(APITestCase):
    
    # region 数据准备
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
        
        print("-----测试数据准备完成-----\n")
        
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        print("\n-----开始执行测试方法-----")
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
        
        print("-----测试数据准备完成-----\n")

    def get_day(self, days, format="%Y-%m-%d"):
        """获取当前日期的前/后days天的日期"""
        today = datetime.datetime.now()
        return (today + datetime.timedelta(days=days)).strftime(format)
    
    # endregion

    # region 基础功能测试
    def test_create_course_with_valid_data(self):
        """测试使用有效数据创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否有data和message
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "not_started")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)
    # endregion

    # region 数据验证测试
    def test_create_course_without_title(self):
        """测试使用无效数据创建课程"""
        data = {
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("name", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_course_without_description(self):
        """测试使用无效数据创建课程"""
        data = {
            "name": "test_name",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)

    def test_create_course_without_start_date(self):
        """测试使用无效数据创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("start_date", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_course_without_end_date(self):
        """测试使用无效数据创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message
        self.assertIn("message", response.data)
        self.assertIn("end_date", response.data["message"])
        # 是否返回data
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"], None)

    def test_create_course_with_start_date_after_end_date(self):
        """测试开始时间晚于结束时间"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=2),
            "end_date": self.get_day(days=1)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 是否返回message 
        self.assertIn("message", response.data)
        self.assertIn("开始时间不得比结束时间迟", response.data["message"])
    # endregion

    # region 权限测试
    def test_create_course_without_login(self):
        """测试未登录用户创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data
        )
        # 是否返回401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_course_with_student(self):
        """测试学生创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        # 是否返回403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_course_with_teacher(self):
        """测试教师创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "not_started")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)

    def test_create_course_with_teacher_with_status_in_progress(self):
        """测试教师创建课程无法自定义状态"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2),
            "status": "in_progress"
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "not_started")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)

    def test_create_course_with_teacher_with_status_completed(self):
        """测试教师创建课程无法自定义状态"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2),
            "status": "completed"
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "not_started")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)

    def test_create_course_with_admin(self):
        """测试管理员创建课程"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.admin)
        self.assertEqual(course.status, "not_started")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)
    # endregion

    # region 业务逻辑测试
    def test_create_course_status_not_started(self):
        """测试创建课程未来开始时状态为not_started"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=1),
            "end_date": self.get_day(days=2)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message   
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "not_started")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)

    def test_create_course_status_in_progress(self):
        """测试创建课程当前进行时状态为in_progress"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=-1),
            "end_date": self.get_day(days=1)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "in_progress")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)

    def test_create_course_status_completed(self):
        """测试创建课程已结束时状态为completed"""
        data = {
            "name": "test_name",
            "description": "test_description",
            "start_date": self.get_day(days=-2),
            "end_date": self.get_day(days=-1)
        }
        response = self.client.post(
            self.url,
            data=data,
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        # 是否返回201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 是否返回message
        self.assertIn("message", response.data)
        # 是否返回data
        self.assertIn("data", response.data)
        # 是否创建成功
        self.assertEqual(Course.objects.count(), 1)
        course = Course.objects.first()
        self.assertEqual(course.name, "test_name")
        self.assertEqual(course.description, "test_description")
        self.assertEqual(course.start_date.strftime("%Y-%m-%d"), data["start_date"])
        self.assertEqual(course.end_date.strftime("%Y-%m-%d"), data["end_date"])
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.status, "completed")
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)
    # endregion
