from rest_framework.test import APITestCase
from rest_framework import status
from subject.models import Subject
from accounts.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os

'''
1. 权限测试：
   [x] 未登录用户尝试删除课题（应该被拒绝）
   [x] 学生用户尝试删除课题（应该被拒绝）
   [x] 教师用户尝试删除自己的课题（应该成功）
   [x] 教师用户尝试删除其他教师的课题（应该被拒绝）
   [x] 管理员用户尝试删除任何课题（应该成功）

2. 数据验证测试：
   [x] 删除不存在的课题ID（应该返回404）
   [x] 删除已删除的课题（应该返回404）
   [x] 删除无效的课题ID格式（应该返回400）

3. 文件处理测试：
   [x] 删除带文件的课题时，文件是否被正确删除
   [x] 删除不带文件的课题时，是否能正常处理

4. 业务逻辑测试：
   - 删除课题后，数据库中的记录是否被正确删除
   - 删除课题后，返回的响应格式是否正确
   - 删除课题后，文件系统中的文件是否被正确删除

5. 关联数据测试：
   - 如果课题有关联的学生选择记录，删除时是否正确处理
   - 如果课题有关联的审核记录，删除时是否正确处理

6. 响应测试：
   - 删除成功时，返回的状态码是否为200
   - 删除成功时，返回的消息是否正确
   - 删除失败时，返回的错误信息是否准确

7. 并发测试：
   - 多个用户同时尝试删除同一个课题时的处理
   - 删除过程中发生异常时的处理

8. 性能测试：
   - 删除大量课题时的性能表现
   - 删除带大文件的课题时的性能表现
'''

MAX_SUBJECTS = 150

class SubjectDeleteTestCase(APITestCase):

        # region 数据准备
    @classmethod
    def setUpTestData(cls):
        """类级别的测试数据准备，只执行一次"""
        print("\n-----开始准备测试数据-----")
        
        # 清空数据库
        Subject.objects.all().delete()
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

        # 删除url
        cls.url = reverse("subject-list")

        # 准备测试课题数据
        cls.subject_data_list = [{
            "title": f"test_title_{i}",
            "description": f"test_description_{i}",
            "max_students": i
        } for i in range(1, MAX_SUBJECTS)]  # 修改这里，创建MAX_SUBJECTS个数据
        
        
        
        print("-----测试数据准备完成-----\n")
    
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        # 清空课题数据，保持数据库干净
        Subject.objects.all().delete()
        
        # 获取token
        self.teacher_token = self.client.post(
            reverse("login"), 
            {"email": self.teacher.email, "password": "teacher123"}
        ).data["data"]["access"]
        
        self.student_token = self.client.post(
            reverse("login"), 
            {"email": self.student.email, "password": "student123"}
        ).data["data"]["access"]
        
        self.admin_token = self.client.post(
            reverse("login"), 
            {"email": self.admin.email, "password": "admin123"}
        ).data["data"]["access"]
    
    def create_subjects(self, count=None, creator=None, status="PENDING"):
        """批量创建测试课题"""
        data_to_create = self.subject_data_list[:count] if count else self.subject_data_list
        subjects = [
            Subject(
                title=data["title"],
                description=data["description"],
                max_students=data["max_students"],
                creator=creator,
                status=status
            ) for data in data_to_create
        ]
        return Subject.objects.bulk_create(subjects)
    # endregion

    # region 权限测试
    def test_unauthorized_user_delete_subject(self):
        """未登录用户尝试删除课题"""
        # 创建一个课题
        self.create_subjects(1, self.teacher, "PENDING")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_delete_subject(self):
        """学生用户尝试删除课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.student_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_delete_subject(self):
        """教师用户尝试删除自己的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_teacher_delete_other_teacher_subject(self):
        """教师用户尝试删除其他教师的课题"""
        self.create_subjects(1, self.teacher2, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete_subject(self):
        """管理员用户尝试删除课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    # endregion

    # region 数据验证测试
    def test_delete_nonexistent_subject(self):
        """删除不存在的课题ID"""
        response = self.client.delete(
            f"{self.url}999999/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_deleted_subject(self):
        """删除已删除的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        subject.delete()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_invalid_subject_id(self):
        """删除无效的课题ID格式"""
        response = self.client.delete(
            f"{self.url}invalid_id/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    # endregion

    # region 文件处理测试
    def test_delete_subject_with_file(self):
        """删除带文件的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        subject.description_file = SimpleUploadedFile("test.txt", content=b"test", content_type="text/plain")
        subject.save()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.exists(subject.description_file.path))
    
    def test_delete_subject_without_file(self):
        """删除不带文件的课题"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    # endregion

    # region 相应测试
    def test_delete_subject_success_response(self):
        """删除成功时，返回的响应格式是否正确"""
        self.create_subjects(1, self.teacher, "APPROVED")
        subject = Subject.objects.first()
        response = self.client.delete(
            f"{self.url}{subject.id}/",
            HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, None)
    # endregion

    
    