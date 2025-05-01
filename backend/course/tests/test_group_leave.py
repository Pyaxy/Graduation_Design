from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from course.models import Course, Group
from accounts.models import User
import datetime
MAX_STUDENTS = 10
MAX_COURSES = 10

class GroupDeleteViewTest(APITestCase):
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

    # region 正常功能测试



        # region 主动退出
    def test_leave_group_with_student(self):
        """测试学生主动退出小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        group.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student)

    def test_leave_group_with_group_owner_and_group_has_other_students(self):
        """测试组长退出小组，小组还有其他学生"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        group.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student2)
        self.assertEqual(group.creator, self.student2)

    def test_leave_group_with_group_owner_and_group_has_only_group_owner(self):
        """测试组长退出小组，小组只有组长一人"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        self.assertEqual(Group.objects.count(), 0)
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Group.objects.count(), 0)
        

    def test_leave_group_with_student_when_group_owner_leave_course_and_group_has_only_group_owner(self):
        """测试只剩组长一人时，组长退出课程，小组被删除"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        # 退出课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/leave/',
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        # 检查小组是否被删除
        self.assertEqual(Group.objects.count(), 0)

    def test_leave_group_with_student_when_group_owner_leave_course_and_group_has_other_students(self):
        """测试小组还有其他人，组长退出课程，小组被转让"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 退出课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/leave/',
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        # 检查小组是否被转让
        self.assertEqual(Group.objects.first().creator, self.student2)
        self.assertEqual(Group.objects.first().students.count(), 1)

    def test_leave_group_with_student_when_student_leave_course(self):
        """测试学生退出课程后，同样退出小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 退出课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/leave/',
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student)
        self.assertEqual(group.creator, self.student)
        # endregion


        # region 提出学生
    def test_leave_group_with_group_owner_leave_student(self):
        """测试组长正常踢出学生"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student)
        self.assertEqual(group.creator, self.student)

    def test_leave_group_with_teacher_leave_his_group_student(self):
        """测试教师踢出自己的学生"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/leave/',
            data={
                "student_user_id": self.student.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group.students.count(), 0)
        self.assertEqual(group.creator, self.teacher)

    def test_leave_group_with_teacher_leave_group_owner(self):
        """测试教师踢出组长"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 踢出组长
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        group.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student2)
        self.assertEqual(group.creator, self.student2)

    def test_leave_group_with_teacher_leave_group_member(self):
        """测试教师踢出小组成员"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)   
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 踢出小组成员
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student)
        self.assertEqual(group.creator, self.student)
        

    def test_leave_group_with_teacher_leave_student_from_course(self):
        """测试教师踢出学生后，学生退出小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student_token)
        self.assertEqual(group.students.count(), 1)
        self.assertEqual(group.students.first(), self.student)
        self.assertEqual(group.creator, self.teacher)
        # 踢出学生
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/leave/',
            data={
                "student_user_id": self.student.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(group.students.count(), 0)
        self.assertEqual(group.creator, self.teacher)
        # endregion



    # endregion



    # region 权限测试
    def test_leave_group_with_student_not_in_course(self):
        """测试学生自己不在课程中，无法主动退出小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_leave_group_with_student_not_in_group(self):
        """测试学生不在小组中，无法退出小组"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_leave_group_with_group_owner_leave_student_not_in_course(self):
        """测试组长踢出学生，学生不在课程中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_group_with_group_owner_leave_student_not_in_group(self):
        """测试组长踢出学生，学生不在小组中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_group_with_group_owner_leave_other_group_student(self):
        """测试组长踢出其他小组的学生"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        response = self.create_group(course.id, token=self.student2_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_leave_group_with_member_leave_student(self):
        """测试非组长踢出学生"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student2_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_group_with_teacher_leave_student_not_in_course(self):
        """测试教师踢出学生，学生不在课程中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_leave_group_with_teacher_leave_student_not_in_group(self):
        """测试教师踢出学生，学生不在小组中"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        response = self.join_course(course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_leave_group_with_teacher_leave_other_course_student(self):
        """测试教师踢出其他课程的学生"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 加入小组
        response = self.join_group(group.id, token=self.student_token)
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": self.student2.user_id
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    # endregion

    # region 异常测试
    def test_leave_group_with_student_with_course_in_progress(self):
        """测试学生无法退出正在进行中的课程"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=-1, end_delta=2)
        course = Course.objects.first()
        # 加入课程
        course.students.add(self.student)
        # 创建小组
        group = Group.objects.create(creator=self.student, course=course)
        # 加入小组
        group.students.add(self.student)
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_group_with_student_with_course_completed(self):
        """测试学生无法退出已结束的课程"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=-1, end_delta=-1)
        course = Course.objects.first()
        # 加入课程
        course.students.add(self.student)
        # 创建小组
        group = Group.objects.create(creator=self.student, course=course)
        # 加入小组
        group.students.add(self.student)
        # 退出小组
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leave_group_with_student_user_id_not_exist(self):
        """测试学生用户ID不存在"""
        # 创建课程
        self.create_courses(1, token=self.teacher_token, start_delta=1, end_delta=2)
        course = Course.objects.first()
        # 创建小组
        response = self.create_group(course.id, token=self.teacher_token)
        group = Group.objects.first()
        # 踢出学生
        response = self.client.post(
            f'{reverse("group-list")}{group.id}/leave/',
            data={
                "student_user_id": "user_id_not_exist"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion
    
    