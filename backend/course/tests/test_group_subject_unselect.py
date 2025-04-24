from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from course.models import Course, CourseSubject, Group, GroupSubject
from subject.models import Subject, PublicSubject
from accounts.models import User
import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
MAX_COURSES = 10
MAX_SUBJECTS = 10
MAX_STUDENTS = 10

class GroupSubjectUnselectTestCase(APITestCase):
    # region 测试数据准备
    @classmethod
    def setUpTestData(cls):
        """类级别的测试数据准备，只执行一次"""
        print("\n-----开始准备测试数据-----")

        # 清空数据库
        Course.objects.all().delete()
        User.objects.all().delete()
        Subject.objects.all().delete()
        PublicSubject.objects.all().delete()

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
        # 准备测试课题数据
        cls.subject_data_list = [{
            "title": f"test_title_{i}",
            "description": f"test_description_{i}",
            "languages": ["C", "CPP", "JAVA", "PYTHON"]
        } for i in range(1, MAX_SUBJECTS)]  # 修改这里，创建MAX_SUBJECTS个数据
        print("-----测试数据准备完成-----\n")

    def setUp(self):
        """每个测试方法执行前的准备工作"""
        # 清空数据库
        Course.objects.all().delete()
        Subject.objects.all().delete()
        PublicSubject.objects.all().delete()
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
    def create_subjects(self, count=None, token=None):
        """批量创建测试课题"""
        data_to_create = self.subject_data_list[:count] if count else self.subject_data_list
        for data in data_to_create:
            self.client.post(
                reverse("subject-list"),
                data={
                "title": data["title"],
                "description": data["description"],
                "languages": data["languages"],
                },
                HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
            )
    
    def create_subject_with_file(self, subject_id, token=None):
        """创建带文件的课题"""
        return self.client.post(
            reverse("subject-list"),
            data={
                "title": "test_title_with_file",
                "description": "test_description_with_file",
                "languages": ["C", "CPP", "JAVA", "PYTHON"],
                "description_file": SimpleUploadedFile("test.txt", content=b'test content', content_type="text/plain")
            },
            format="multipart",
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
        )

    def review_subjects(self, subject_id, status="APPROVED"):
        """审核课题"""
        return self.client.post(
            f"{reverse('subject-list')}{subject_id}/review/",
            data={
                "status": status,
                "review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
    
    def apply_public(self, subject_id, token=None):
        """申请公开课题"""
        return self.client.post(
            f"{reverse('subject-list')}{subject_id}/apply-public/",
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
        )
    
    def review_public(self, subject_id, token=None):
        """审核公开课题"""
        return self.client.post(
            f"{reverse('subject-list')}{subject_id}/review-public/",
            data={
                "public_status": "APPROVED",
                "public_review_comments": "审核通过"
            },
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.admin_token}"
        )
    
    def add_subject_to_course(self, course_id, subject_id, token=None):
        """添加课题到课程"""
        return self.client.post(
            f'{reverse("course-list")}{course_id}/add_subject/',
            data={
                "subject_ids": f'{subject_id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.teacher_token}"
        )
    def select_subject(self, group_id, course_subject_id, token=None):
        """选择课题"""
        return self.client.post(
            f"{reverse('group-list')}{group_id}/select_subject/",
            data={"course_subject_id": course_subject_id},
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.student_token}"
        )
    # endregion

    # region 正常功能测试
    def test_unselect_subject_with_student(self):
        """学生退选课题"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course_code=course.course_code, token=self.student_token)
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        self.add_subject_to_course(course_id=course.id, subject_id=subject.id, token=self.teacher_token)
        course_subject = CourseSubject.objects.first()
        # 创建小组
        response = self.create_group(course_id=course.id, token=self.student_token)
        group = Group.objects.first()
        # 选择课题
        self.select_subject(group_id=group.id, course_subject_id=course_subject.id, token=self.student_token)
        # 退选课题
        response = self.client.delete(
            f"{reverse('group-list')}{group.id}/unselect_subject/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 验证退选课题
        self.assertFalse(GroupSubject.objects.filter(group=group, course_subject=course_subject).exists())
    # endregion

    # region 异常功能测试
    def test_unselect_subject_with_student_not_group_member(self):
        """学生退选课题，非小组成员"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course_code=course.course_code, token=self.student_token)
        self.join_course(course_code=course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course_id=course.id, token=self.student_token)
        group = Group.objects.first()
        # 退选课题
        response = self.client.delete(
            f"{reverse('group-list')}{group.id}/unselect_subject/",
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unselect_subject_with_student_not_course_member(self):
        """学生退选课题，非课程成员"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course_code=course.course_code, token=self.student_token)
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        self.add_subject_to_course(course_id=course.id, subject_id=subject.id, token=self.teacher_token)
        course_subject = CourseSubject.objects.first()
        # 创建小组
        response = self.create_group(course_id=course.id, token=self.student_token)
        group = Group.objects.first()
        # 退选课题
        response = self.client.delete(
            f"{reverse('group-list')}{group.id}/unselect_subject/",
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unselect_subject_with_group_not_found(self):
        """退选课题，小组不存在"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course_code=course.course_code, token=self.student_token)
        # 退选课题
        response = self.client.delete(
            f"{reverse('group-list')}1234567890/unselect_subject/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unselect_subject_with_course_subject_not_found(self):
        """退选课题，未选课题"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course_code=course.course_code, token=self.student_token)
        # 创建小组
        response = self.create_group(course_id=course.id, token=self.student_token)
        group = Group.objects.first()
        # 退选课题
        response = self.client.delete(
            f"{reverse('group-list')}{group.id}/unselect_subject/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    # endregion
    
    # region 权限测试
    def test_unselect_subject_with_student_not_group_creator(self):
        """学生退选课题，非小组创建者"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 加入课程
        self.join_course(course_code=course.course_code, token=self.student_token)
        self.join_course(course_code=course.course_code, token=self.student2_token)
        # 创建小组
        response = self.create_group(course_id=course.id, token=self.student_token)
        group = Group.objects.first()
        # 加入小组
        self.join_group(group_id=group.id, token=self.student2_token)
        # 退选课题
        response = self.client.delete(
            f"{reverse('group-list')}{group.id}/unselect_subject/",
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    # endregion
