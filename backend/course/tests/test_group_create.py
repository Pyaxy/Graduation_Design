from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from course.models import Course, Group
from accounts.models import User
import datetime
MAX_STUDENTS = 10
MAX_COURSES = 10

class GroupCreateViewTest(APITestCase):
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
        cls.url = reverse("group-list")
        cls.course_data_list = [
            {
                "name": f"test_course_{i}",
                "description": f"test_description_{i}",
                "max_group_size": 3,
                "min_group_size": 1
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
                "end_date": self.get_day(days=end_delta),
                "max_group_size": data["max_group_size"],
                "min_group_size": data["min_group_size"]
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

    # region 正常功能测试
    def test_create_group_with_student(self):
        """测试学生创建小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.first()
        self.assertEqual(group.course, course)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student)
        # 检查小组名称是否正确
        self.assertEqual(group.name, f"{course.name} 小组 1")
        # 检查小组创建者是否正确
        self.assertEqual(group.creator, self.student)

    def test_create_group_with_teacher(self):
        """测试教师创建小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.first()
        self.assertEqual(group.course, course)
        self.assertEqual(group.students.count(), 0)
        self.assertEqual(group.creator, self.teacher)
        # 检查小组名称是否正确
        self.assertEqual(group.name, f"{course.name} 小组 1")
        # 检查小组创建者是否正确
        self.assertEqual(group.creator, self.teacher)
        self.assertEqual(group.max_students, course.max_group_size)
        self.assertEqual(group.min_students, course.min_group_size)

    # endregion

    # region 异常状态测试
    def test_create_group_with_student_not_in_course(self):
        """测试学生创建小组时不在课程中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 0)
        # 是否有message
        self.assertEqual(response.data["message"], "未查询到该课程")

    def test_create_group_with_student_already_joined_group(self):
        """测试学生创建小组时已经在其他小组中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 1)
        # 是否有message
        self.assertIn("您已经加入了小组", response.data["message"])

    def test_create_group_with_teacher_not_in_course(self):
        """测试教师创建小组时不在课程中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 0)
        # 是否有message
        self.assertEqual(response.data["message"], "未查询到该课程")

    def test_create_group_with_course_in_progress(self):
        """测试课程进行中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=-1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 0)
        # 是否有message
        self.assertIn("课程已开始", response.data["message"])

    def test_create_group_with_course_completed(self):
        """测试课程已结束"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=-2, end_delta=-1)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 0)
        # 是否有message
        self.assertIn("课程已结束", response.data["message"])
    # endregion

    # region 权限测试
    def test_create_group_with_unauthorized_user(self):
        """测试未授权用户创建小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 检查小组是否创建成功
        self.assertEqual(Group.objects.count(), 0)
    # endregion

    # region 小组自动生成名称测试
    def test_group_auto_generate_group_name(self):
        """测试小组自动生成名称"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查小组名称是否正确
        self.assertEqual(Group.objects.first().name, f"{course.name} 小组 1")
        # 创建第二个小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查小组名称是否正确
        self.assertEqual(Group.objects.first().name, f"{course.name} 小组 2")

    def test_group_auto_generate_group_name_when_group_deleted(self):
        """测试小组删除后自动生成名称"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查小组名称是否正确
        self.assertEqual(Group.objects.first().name, f"{course.name} 小组 1")
        # 删除小组
        Group.objects.first().delete()
        # 创建小组
        response = self.client.post(
            self.url,
            data={
                "course": course.id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查小组名称是否正确
        self.assertEqual(Group.objects.last().name, f"{course.name} 小组 1")
    # endregion
    