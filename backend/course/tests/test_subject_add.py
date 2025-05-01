from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from course.models import Course, CourseSubject
from subject.models import Subject, PublicSubject
from django.urls import reverse
import datetime

MAX_COURSES = 10
MAX_STUDENTS = 10
MAX_SUBJECTS = 10

class AddSubjectTestCase(APITestCase):
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

    # endregion
    
    # region 正常测试功能
    def test_add_subject_to_course_with_teacher_add_private_subject(self):
        """教师添加私有课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        subject.refresh_from_db()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 1)
        self.assertEqual(CourseSubject.objects.first().private_subject, subject)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["success"]["ids"], [subject.id])
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["details"], [])

    def test_add_subject_to_course_with_teacher_add_public_subject(self):
        """教师添加公开课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 申请公开课题
        self.apply_public(subject_id=subject.id, token=self.teacher_token)
        # 审核公开课题
        self.review_public(subject_id=subject.id, token=self.admin_token)
        public_subject = PublicSubject.objects.first()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{public_subject.id}',
                "subject_type": "PUBLIC"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 1)
        self.assertEqual(CourseSubject.objects.first().public_subject, public_subject)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["success"]["ids"], [public_subject.id])
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["details"], [])

    def test_add_subject_to_course_with_admin_add_any_teacher_subject(self):
        """管理员添加任何教师创建的课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        self.create_subjects(count=1, token=self.teacher2_token)
        subject2 = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        self.review_subjects(subject_id=subject2.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id},{subject2.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        subject.refresh_from_db()
        subject2.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 2)
        self.assertEqual(CourseSubject.objects.first().private_subject, subject2)
        self.assertEqual(CourseSubject.objects.last().private_subject, subject)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 2)
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["success"]["ids"], [subject.id, subject2.id])
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["details"], [])
        
    def test_add_subject_to_course_with_admin_add_public_subject(self):
        """管理员添加公开课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 申请公开课题
        self.apply_public(subject_id=subject.id, token=self.teacher_token)
        # 审核公开课题
        self.review_public(subject_id=subject.id, token=self.admin_token)
        public_subject = PublicSubject.objects.first()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{public_subject.id}',
                "subject_type": "PUBLIC"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 1)
        self.assertEqual(CourseSubject.objects.first().public_subject, public_subject)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["success"]["ids"], [public_subject.id])
        self.assertEqual(response.data["data"]["failed"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["details"], [])
        

    def test_add_subject_to_course_with_teacher_add_subject_one_success_one_failed(self):
        """教师添加课题到课程，一个成功一个失败"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=2, token=self.teacher_token)
        subject = Subject.objects.first()
        subject2 = Subject.objects.last()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id},{subject2.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 1)
        self.assertEqual(CourseSubject.objects.first().private_subject, subject)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["count"], 1)
        self.assertEqual(response.data["data"]["success"]["ids"], [subject.id])
        self.assertEqual(response.data["data"]["failed"]["details"][0]["id"], subject2.id)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["reason"], "课题未审核通过")
        
        
    # endregion

    # region 权限测试
    def test_add_subject_to_course_with_student_who_in_course(self):
        """课程中学生添加课题到课程"""
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
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_add_subject_to_course_with_student_who_not_in_course(self):
        """未加入课程的学生添加课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_subject_to_course_with_teacher_not_create_course(self):
        """未创建课程的教师添加课题到课程"""
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")  
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_subject_to_course_with_teacher_not_create_subject(self):
        """教师添加别的老师的私有课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher2_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 0)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["id"], subject.id)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["reason"], "您没有权限添加此课题")

    # endregion

    # region 异常测试
    def test_add_subject_to_course_with_teacher_add_private_subject_not_approved(self):
        """教师添加未审核的私有课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 0)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["id"], subject.id)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["reason"], "课题未审核通过")

    def test_add_subject_to_course_with_teacher_add_private_subject_rejected(self):
        """教师添加被拒绝的私有课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 拒绝课题
        self.review_subjects(subject_id=subject.id, status="REJECTED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 0)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["id"], subject.id)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["reason"], "课题未审核通过")
        
        
    def test_add_subject_to_course_with_teacher_add_public_subject_not_approved(self):
        """教师添加未审核的公开课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 申请公开课题
        self.apply_public(subject_id=subject.id, token=self.teacher_token)
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PUBLIC"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 0)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["id"], subject.id)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["reason"], "公开课题不存在")

    def test_add_subject_to_course_with_teacher_readd_subject_to_course(self):
        """教师重复添加课题到课程"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 重复添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查课题是否添加成功
        self.assertEqual(CourseSubject.objects.count(), 1)

        # 检查返回数据
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data["data"])
        self.assertIn("failed", response.data["data"])
        self.assertIn("count", response.data["data"]["success"])
        self.assertIn("ids", response.data["data"]["success"])
        self.assertIn("count", response.data["data"]["failed"])
        self.assertIn("details", response.data["data"]["failed"])
        self.assertEqual(response.data["data"]["success"]["count"], 0)
        self.assertEqual(response.data["data"]["failed"]["count"], 1)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["id"], subject.id)
        self.assertEqual(response.data["data"]["failed"]["details"][0]["reason"], "该课题已经添加到课程中")
        
    # endregion

    # region 状态测试
    def test_add_subject_to_course_with_teacher_add_subject_when_course_is_in_progress(self):
        """课程进行中时添加课题"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token, start_delta=-1, end_delta=2)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_subject_to_course_with_teacher_add_subject_when_course_is_completed(self):
        """课程结束后添加课题"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token, start_delta=-2, end_delta=-1)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        self.review_subjects(subject_id=subject.id, status="APPROVED")
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    # endregion

    # region 数据验证
    def test_add_subject_to_course_with_teacher_add_subject_with_invalid_subject_ids(self):
        """教师添加课题到课程，课题ID无效"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": "invalid_subject_id",
                "subject_type": "PRIVATE"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_subject_to_course_with_teacher_add_subject_with_invalid_subject_type(self):
        """教师添加课题到课程，课题类型无效"""
        # 创建课程
        self.create_courses(count=1, token=self.teacher_token)
        course = Course.objects.first()
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 添加课题到课程
        response = self.client.post(
            f'{reverse("course-list")}{course.id}/add_subject/',
            data={
                "subject_ids": f'{subject.id}',
                "subject_type": "INVALID"   
            },
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    # endregion