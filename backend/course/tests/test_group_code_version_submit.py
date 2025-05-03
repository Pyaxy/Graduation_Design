from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from course.models import Course, CourseSubject, Group, GroupSubject, GroupCodeVersion, GroupSubmission, GroupSubmissionContribution
from subject.models import Subject, PublicSubject
from accounts.models import User
import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
import os
MAX_COURSES = 10
MAX_SUBJECTS = 10
MAX_STUDENTS = 10

class GroupCodeVersionSubmitTestCase(APITestCase):
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
        GroupCodeVersion.objects.all().delete()
        
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
    
    def create_course_and_subject_and_group(self):
        """创建课程，学生1加入课程，学生1创建小组，学生1选择课题"""
        # 创建课程
        self.create_courses(count=1)
        course = Course.objects.first()
        # 加入课程
        response = self.join_course(course_code=course.course_code, token=self.student_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 创建课题
        self.create_subjects(count=1, token=self.teacher_token)
        subject = Subject.objects.first()
        # 审核课题
        response = self.review_subjects(subject_id=subject.id, status="APPROVED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 加入课题
        response = self.add_subject_to_course(course_id=course.id, subject_id=subject.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course_subject = CourseSubject.objects.first()
        # 创建小组
        response = self.create_group(course_id=course.id, token=self.student_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group = Group.objects.first()
        # 选择课题
        response = self.select_subject(group_id=group.id, course_subject_id=course_subject.id, token=self.student_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return course, subject, group, course_subject
    
    def update_course_status(self, course_id, status):
        """更新课程状态"""
        course = Course.objects.get(id=course_id)
        if status == "not_started":
            start_date = self.get_day(days=1)
            end_date = self.get_day(days=2)
        elif status == "in_progress":
            start_date = self.get_day(days=-1)
            end_date = self.get_day(days=1)
        elif status == "completed":
            start_date = self.get_day(days=-2)
            end_date = self.get_day(days=-1)
        response = self.client.put(
            f"{reverse('course-list')}{course_id}/",
            data={
                "name": course.name,
                "description": course.description,
                "start_date": start_date,
                "end_date": end_date,
            },
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
    
    def get_test_zip_file(self):
        """获取测试ZIP文件"""
        test_zip_path = os.path.join(f'{os.path.dirname(__file__)}/test_files', 'test_zip_file.zip')
        with open(test_zip_path, 'rb') as f:
            zip_file = SimpleUploadedFile(
                name='test_zip_file.zip',
                content=f.read(),
                content_type='application/zip'
            )
        return zip_file
    def create_group_code_version(self, version, group, token=None):
        """创建小组代码版本"""
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/versions/",
            data={
                'version': version,
                'description': 'test_description',
                "zip_file": self.get_test_zip_file()
            },
            HTTP_AUTHORIZATION=f"Bearer {token if token else self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def get_group_list(self, course_id, token=None):
        """获取小组列表"""
        response = self.client.get(
            f"{self.url}?course_id={course_id}",
            headers={"Authorization": f"Bearer {token if token else self.teacher_token}"}
        )
        return response.data["data"]["results"]
    # endregion

    # region 正常测试
    def test_submit_code_version(self):
        """测试提交代码版本"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 小组列表没有提交记录
        group_list = self.get_group_list(course_id=course.id, token=self.student_token)
        self.assertFalse(group_list[0]["submission"]["is_submitted"])
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 检查提交记录是否存在
        submission = GroupSubmission.objects.first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.group, group)
        self.assertEqual(submission.code_version, version)
        self.assertTrue(submission.is_submitted)
        self.assertIsNotNone(submission.submitted_at)
        # 检查贡献度是否存在
        contribution = GroupSubmissionContribution.objects.first()
        self.assertIsNotNone(contribution)
        self.assertEqual(contribution.submission, submission)
        self.assertEqual(contribution.student, self.student)
        self.assertEqual(contribution.contribution, 100)
        # 检查小组列表是否包含提交记录
        group_list = self.get_group_list(course_id=course.id, token=self.student_token)
        self.assertEqual(len(group_list), 1)
        self.assertTrue(group_list[0]["submission"])
    # endregion

    # region 异常测试
    def test_submit_code_version_with_invalid_code_version_id(self):
        """测试提交代码版本，代码版本ID无效"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": "invalid_code_version_id",
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_code_version_with_invalid_group_id(self):
        """测试提交代码版本，小组ID无效"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}invalid_group_id/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_code_version_with_course_not_in_progress(self):
        """测试提交代码版本，课程未进行中"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为未开始
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        self.update_course_status(course_id=course.id, status="not_started")
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_code_version_with_course_completed(self):
        """测试提交代码版本，课程已完成"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为已完成
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        self.update_course_status(course_id=course.id, status="completed")
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_code_version_with_version_not_in_group(self):
        """测试提交代码版本，代码版本不属于该小组"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.create_group(course_id=course.id, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        group2 = Group.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group2.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_code_version_with_group_not_selected_subject(self):
        """测试提交代码版本，小组未选择课题"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.create_group(course_id=course.id, token=self.student2_token)
        group2 = Group.objects.first()
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group2.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_code_version_with_contribution_not_include_all_students(self):
        """测试提交代码版本，贡献度不包含所有学生"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.join_group(group_id=group.id, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("缺少以下学生的贡献度: student1", response.data["message"])

    def test_submit_code_version_with_contribution_not_in_0_100(self):
        """测试提交代码版本，贡献度不在0-100之间"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 101
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("贡献度必须在0-100之间", response.data["message"])

    def test_submit_code_version_with_total_contribution_not_100(self):
        """测试提交代码版本，贡献度总和不为100"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.join_group(group_id=group.id, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 50
                    },
                    {
                        "student_id": self.student2.user_id,
                        "contribution": 30
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("所有学生的贡献度之和必须为100", response.data["message"])
        
    def test_submit_code_version_with_repeat_contribution(self):
        """测试提交代码版本，贡献度重复"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.join_group(group_id=group.id, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 50
                    },
                    {
                        "student_id": self.student2.user_id,
                        "contribution": 50
                    },
                    {
                        "student_id": self.student.user_id,
                        "contribution": 50
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("贡献度重复提交", response.data["message"])

    def test_submit_code_version_with_contribution_not_number(self):
        """测试提交代码版本，贡献度不是数字"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": "not_number"
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("贡献度必须是数字", response.data["message"])

    def test_submit_code_version_without_contribution(self):
        """测试提交代码版本，没有贡献度"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": []
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_code_version_with_repeat_submit(self):
        """测试提交代码版本，重复提交"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.join_group(group_id=group.id, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    },
                    {
                        "student_id": self.student2.user_id,
                        "contribution": 0
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        print('******************', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    },
                    {
                        "student_id": self.student2.user_id,
                        "contribution": 0
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("小组已经提交过代码", response.data["message"])
    # endregion

    # region 权限测试
    def test_submit_code_version_with_student_not_in_group(self):
        """测试提交代码版本，学生不在小组中"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submit_code_version_with_not_group_creator(self):
        """测试提交代码版本，非小组创建者"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        self.join_course(course_code=course.course_code, token=self.student2_token)
        self.join_group(group_id=group.id, token=self.student2_token)
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_submit_code_version_with_student_not_in_course(self):
        """测试提交代码版本，学生不在课程中"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student2_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_code_version_with_student_contribution_not_in_group(self):
        """测试提交代码版本中，学生贡献度不在小组中"""
        # 创建课程，学生1加入课程，学生1创建小组，学生1选择课题
        course, subject, group, course_subject = self.create_course_and_subject_and_group()
        # 更新课程状态为进行中
        self.update_course_status(course_id=course.id, status="in_progress")
        # 创建小组代码版本
        self.create_group_code_version(version="1.0", group=group, token=self.student_token)
        version = GroupCodeVersion.objects.first()
        # 提交代码版本
        response = self.client.post(
            f"{reverse('group-list')}{group.id}/submit_code/",
            data={
                "code_version_id": version.id,
                "contributions": [
                    {
                        "student_id": self.student2.user_id,
                        "contribution": 100
                    }
                ]
            },
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("不在该小组中", response.data["message"])
    # endregion