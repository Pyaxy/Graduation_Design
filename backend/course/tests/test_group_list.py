from rest_framework.test import APITestCase
from rest_framework import status
from course.models import Group, Course, User
from django.urls import reverse
import datetime

MAX_COURSES = 10
MAX_STUDENTS = 10

class GroupListViewTest(APITestCase):
    # region 测试数据准备
    @classmethod
    def setUpTestData(cls):
        """类级别的测试数据准备，只执行一次"""
        print("\n-----开始准备测试数据-----")

        # 清空数据库
        Course.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

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
        cls.student2 = User.objects.create_user(
            email="student1@example.com",
            password="student123",
            user_id="student001",
            name="student1",
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
            for i in range(2, MAX_STUDENTS + 1)
        ]
        cls.url = reverse("group-list")
        cls.course_data_list = [
            {
                "name": f"test_course_{i}",
                "description": f"test_description_{i}",
                "max_group_size": 3,
                "min_group_size": 1,
                "max_subject_selections": 1
            }
            for i in range(1, MAX_COURSES + 1)
        ]
        print("-----测试数据准备完成-----\n")

    def setUp(self):
        """每个测试方法执行前的准备工作"""
        # 清空数据库
        Course.objects.all().delete()
        Group.objects.all().delete()
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
        self.student2_token = self.client.post(
            reverse("login"),
            {"email": self.student2.email, "password": "student123"}
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

    def create_group(self, course_id, token=None):
        """创建小组"""
        return self.client.post(
            reverse("group-list"),
            data={
                "course": course_id
            },
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.student_token}"
        )
    
    def join_group(self, group_id, token=None):
        """加入小组"""
        return self.client.post(
            f"{reverse('group-list')}{group_id}/join/",
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.student_token}"
        )
    # endregion

    # region 测试列表
    def test_group_list_with_teacher(self):
        """测试教师访问时能正确返回数据列表"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        response = self.create_group(course.id, token=self.teacher_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回数据
        self.assertEqual(response.data["data"]["count"], 2)
        self.assertEqual(len(response.data["data"]["results"]), 2)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_group_list_with_student(self):
        """测试学生访问时能正确返回数据列表"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回数据
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_group_list_with_empty_database(self):
        """测试空数据库时返回空列表"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回数据
        self.assertEqual(response.data["data"]["count"], 0)
        self.assertEqual(len(response.data["data"]["results"]), 0)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion

    # region 测试权限
    def test_group_list_with_unauthorized_user(self):
        """测试未授权用户访问时返回401"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_group_list_with_student_only_see_joined_courses(self):
        """测试学生访问时只能看到已加入的课程"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回数据
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)

        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_group_list_with_student_can_not_see_not_joined_courses(self):
        """测试学生访问时不能看到未加入的课程"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
        
    def test_group_list_with_teacher_can_not_see_other_teacher_courses(self):
        """测试教师访问时不能看到其他教师的课程小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course.id}",
            headers={"Authorization": f"Bearer {self.teacher2_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion

    # region 边界测试
    def test_group_list_with_teacher_have_two_courses(self):
        """测试教师访问时能正确返回两个课程的小组列表"""
        # 创建课程
        self.create_courses(2, token=self.teacher_token, start_delta=1, end_delta=2)
        course1 = Course.objects.first()
        course2 = Course.objects.last()
        # 创建小组
        response = self.create_group(course1.id, token=self.teacher_token)
        response = self.create_group(course2.id, token=self.teacher_token)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course1.id}",
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回数据
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        # 检查返回数据中的课程ID
        self.assertEqual(response.data["data"]["results"][0]["course"], course1.id)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)

    def test_group_list_with_student_have_two_courses(self):
        """测试学生访问时能正确返回两个课程的小组列表"""
        # 创建课程
        self.create_courses(2, token=self.teacher_token, start_delta=1, end_delta=2)
        course1 = Course.objects.first()
        course2 = Course.objects.last()
        # 加入课程
        response = self.join_course(course1.course_code, token=self.student_token)
        response = self.join_course(course2.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course1.id, token=self.student_token)
        response = self.create_group(course2.id, token=self.student_token)
        # 访问列表
        response = self.client.get(
            f"{self.url}?course_id={course1.id}",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回数据
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        # 检查返回数据中的课程ID
        print(response.data["data"]["results"])
        self.assertEqual(response.data["data"]["results"][0]["course"], course1.id)
        # 是否有message和data
        self.assertIn("message", response.data)
        self.assertIn("data", response.data)
    # endregion
