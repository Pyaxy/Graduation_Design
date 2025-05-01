"""
测试用例:
[x]: 正常加入
[x]: 加入已满的小组
[x]: 组长加入已加入的小组
[x]: 组长加入其他小组
[x]: 组员加入已加入的小组
[x]: 组员加入其他小组
[x]: 加入多个小组
[x]: 加入未加入课程的小组
[x]: 加入未开始课程的小组
[x]: 加入已结束课程的小组
[x]: 加入不存在的小组
[x]: 加入未授权的小组
"""

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse
from course.models import Group, Course
from accounts.models import User
import datetime

MAX_STUDENTS = 10
MAX_COURSES = 10

class GroupJoinViewTest(APITestCase):
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
            email="student2@example.com",
            password="student123",
            user_id="student001",
            name="student2",
            school="student school",
            role="STUDENT"
        )
        cls.students = [
            User.objects.create_user(
                email=f"bulk_student{i}@example.com",
                password="student123",
                user_id=f"bulk_student00{i}",
                name=f"bulk_student{i}",
                school="bulk_student school",
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
    
    def create_courses(self, start_delta=1, end_delta=2, token=None, name="test_course", description="test_description", max_group_size=3, min_group_size=1):
        """创建测试课程"""
        return self.client.post(
                reverse("course-list"),
                data={
                "name": name,
                "description": description,
                "start_date": self.get_day(days=start_delta),
                "end_date": self.get_day(days=end_delta),
                "max_group_size": max_group_size,
                "min_group_size": min_group_size,
                "max_subject_selections": 3
                },
                HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
            )
    def bulk_create_courses(self, count=None, start_delta=1, end_delta=2, token=None):
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
            data={"course": course_id},
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.student_token}"
        )

    # endregion

    # region 正常测试加入小组
    def test_join_group_success(self):
        """测试正常加入小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证是否加入成功
        self.assertEqual(group.students.count(), 2)
        # 使用过滤方式验证学生是否在小组中
        self.assertTrue(group.students.filter(user_id=self.student2.user_id).exists())
        
    # endregion

    # region 异常测试加入小组
    def test_join_group_full(self):
        """测试加入已满的小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2, min_group_size=1, max_group_size=1)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(group.students.count(), 1)
        # 使用过滤方式验证学生是否在小组中
        self.assertFalse(group.students.filter(user_id=self.student2.user_id).exists())

    def test_join_group_with_group_owner_already_joined_group(self):
        """测试组长加入已加入的小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(group.students.count(), 1)
        # 使用过滤方式验证学生是否在小组中
        self.assertTrue(group.students.filter(user_id=self.student.user_id).exists())
    
    def test_join_group_with_group_owner_join_other_group(self):
        """测试组长加入其他小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        stu1_group = Group.objects.first()
        response = self.create_group(course.id, token=self.student2_token)
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{stu1_group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(stu1_group.students.count(), 1)
        self.assertTrue(stu1_group.students.filter(user_id=self.student.user_id).exists())
    
    def test_join_group_with_student_already_joined_group(self):
        """测试组员加入已加入的小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证是否加入成功
        self.assertEqual(group.students.count(), 2)

        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(group.students.count(), 2)

    def test_join_group_with_student_join_other_group(self):
        """测试组员加入其他小组"""
        # 创建课程
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        stu1_group = Group.objects.first()
        response = self.create_group(course.id, token=self.student2_token)
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{stu1_group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(stu1_group.students.count(), 1)
        self.assertTrue(stu1_group.students.filter(user_id=self.student.user_id).exists())
    
    def test_join_group_with_course_in_progress(self):
        """测试加入进行中的课程"""
        # 创建课程
        self.create_courses(start_delta=-1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        course.students.add(self.student)
        course.students.add(self.student2)
        course.save()
        # 创建小组
        group = Group.objects.create(course=course, creator=self.student)
        group.students.add(self.student)
        group.save()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        print(course.status + "====-=-=-=-=-=-=-=-=-====")
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(group.students.count(), 1)
        self.assertIn("课程已开始", response.data["message"])

    def test_join_group_with_course_completed(self):
        """测试加入已结束的课程"""
        # 创建课程
        self.create_courses(start_delta=-2, end_delta=-1)
        course = Course.objects.first()
        # 加入课程
        course.students.add(self.student)
        course.students.add(self.student2)
        course.save()
        # 创建小组
        group = Group.objects.create(course=course, creator=self.student)
        group.students.add(self.student)
        group.save()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 验证是否加入失败
        self.assertEqual(group.students.count(), 1)
        self.assertIn("课程已结束", response.data["message"])

    def test_join_group_with_course_not_exist(self):
        """测试加入不存在的课程"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}123/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion

    # region 权限测试
    def test_join_group_with_studen_not_join_course(self):
        """测试未加入课程的学生加入小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # 验证是否加入失败
        self.assertEqual(group.students.count(), 1)

    def test_join_group_with_unauthorized_user(self):
        """测试未授权的用户加入小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_join_group_with_teacher(self):
        """测试教师加入小组"""
        # 创建课程
        self.create_courses(start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 加入小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/join/',
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    # endregion
