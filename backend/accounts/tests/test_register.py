from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User

class RegisterAPITestCase(APITestCase):
    """用户注册接口测试"""

    @classmethod
    def setUpClass(cls):
        """整个测试类开始时执行一次"""
        print("\n=== setUpClass 开始 ===")
        super().setUpClass()
        # 清理数据库
        User.objects.all().delete()
        print("数据库已清理")
        # 创建管理员用户
        try:
            cls.admin = User.objects.create_superuser(
                email='admin@example.com',
                password='admin123',
                user_id='admin001',
                name='Admin',
                school='Admin School',
                role='ADMIN'
            )
            print("管理员用户创建成功")
        except Exception as e:
            print(f"创建管理员用户失败: {str(e)}")
            raise
        # 创建普通用户
        try:
            cls.user = User.objects.create_user(
                email='user@example.com',
                password='user123',
                user_id='user001',
                name='User',
                school='User School',
                role='STUDENT'
            )
            print("普通用户创建成功")
        except Exception as e:
            print(f"创建普通用户失败: {str(e)}")
            raise
        print("=== setUpClass 结束 ===\n")

    def setUp(self):
        """每个测试方法执行前都会执行"""
        print("\n--- setUp 开始 ---")
        # 获取管理员token
        self.admin_token = self.get_token('admin@example.com', 'admin123')
        print("管理员token获取成功")
        # 获取普通用户token
        self.user_token = self.get_token('user@example.com', 'user123')
        print("普通用户token获取成功")
        # 测试数据
        self.valid_payload = {
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'user_id': 'testuser001',
            'name': 'Test User',
            'school': 'Test School'
        }
        # 注册url
        self.register_url = reverse('register')
        print("--- setUp 结束 ---\n")

    @classmethod
    def tearDownClass(cls):
        """整个测试类结束时执行一次"""
        print("\n=== tearDownClass 开始 ===")
        # 清理数据库
        User.objects.all().delete()
        print("数据库已清理")
        super().tearDownClass()
        print("=== tearDownClass 结束 ===\n")

    def get_token(self, email, password):
        """获取用户token"""
        url = reverse('login')
        response = self.client.post(url, {
            'email': email,
            'password': password
        })
        return response.data['data']['access']

    def test_register_with_admin_token(self):
        """测试管理员注册教师"""
        print("\n运行 test_register_with_admin_token")
        url = reverse('register')
        data = {
            'email': 'teacher@example.com',
            'password': 'teacher123',
            'confirm_password': 'teacher123',
            'user_id': 'teacher001',
            'name': 'Teacher',
            'school': 'Teacher School',
            'role': 'TEACHER'
        }
        # 使用管理员token进行请求
        response = self.client.post(
            url,
            data,
            HTTP_AUTHORIZATION=f'Bearer {self.admin_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], '注册成功')
        self.assertTrue(User.objects.filter(email='teacher@example.com').exists())

    def test_register_with_user_token(self):
        """测试普通用户注册教师"""
        print("\n运行 test_register_with_user_token")
        url = reverse('register')
        data = {
            'email': 'teacher2@example.com',
            'password': 'teacher123',
            'confirm_password': 'teacher123',
            'user_id': 'teacher002',
            'name': 'Teacher2',
            'school': 'Teacher School',
            'role': 'TEACHER'
        }
        # 使用普通用户token进行请求
        response = self.client.post(
            url,
            data,
            HTTP_AUTHORIZATION=f'Bearer {self.user_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], '只有管理员可以注册教师账号')

    def test_register_without_token(self):
        """测试未登录用户注册"""
        print("\n运行 test_register_without_token")
        url = reverse('register')
        data = {
            'email': 'student@example.com',
            'password': 'student123',
            'confirm_password': 'student123',
            'user_id': 'student001',
            'name': 'Student',
            'school': 'Student School',
            'role': 'STUDENT'
        }
        # 不提供token进行请求
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], '注册成功')
        self.assertTrue(User.objects.filter(email='student@example.com').exists())

    def test_register_with_invalid_token(self):
        """测试使用无效token注册"""
        print("\n运行 test_register_with_invalid_token")
        url = reverse('register')
        data = {
            'email': 'teacher3@example.com',
            'password': 'teacher123',
            'confirm_password': 'teacher123',
            'user_id': 'teacher003',
            'name': 'Teacher3',
            'school': 'Teacher School',
            'role': 'TEACHER'
        }
        # 使用无效token进行请求
        response = self.client.post(
            url,
            data,
            HTTP_AUTHORIZATION='Bearer invalid_token'
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], 'Token is invalid')

    def test_register_success(self):
        """测试注册成功"""
        print("\n运行 test_register_success")
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], '注册成功')
        self.assertTrue(User.objects.filter(email=self.valid_payload['email']).exists())

    def test_register_with_default_role(self):
        """测试注册时使用默认role"""
        print("\n运行 test_register_with_default_role")
        payload = self.valid_payload.copy()
        payload.pop('role', None)  # 移除role字段
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证用户是否创建成功，且role为默认值
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.role, 'STUDENT')

    def test_register_with_missing_fields(self):
        """测试缺少必填字段"""
        print("\n运行 test_register_with_missing_fields")
        # 测试缺少多个字段
        payload = {}
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '请填写以下必填项：邮箱, 密码, 确认密码, 学号, 姓名, 学校')

        # 测试缺少单个字段
        payload = self.valid_payload.copy()
        payload.pop('email')
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '请填写以下必填项：邮箱')

        # 测试缺少多个特定字段
        payload = self.valid_payload.copy()
        payload.pop('name')
        payload.pop('school')
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '请填写以下必填项：姓名, 学校')

    def test_register_with_password_mismatch(self):
        """测试密码不匹配"""
        print("\n运行 test_register_with_password_mismatch")
        payload = self.valid_payload.copy()
        payload['confirm_password'] = 'differentpassword'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '两次输入的密码不一致')

    def test_register_with_duplicate_email(self):
        """测试重复邮箱"""
        print("\n运行 test_register_with_duplicate_email")
        # 先创建一个用户
        User.objects.create_user(
            email=self.valid_payload['email'],
            password=self.valid_payload['password'],
            user_id='B2024002',
            name='另一个用户',
            school='北京大学',
            role='STUDENT'
        )

        # 尝试用相同的邮箱注册
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('已存在', response.data['message'])

    def test_register_with_duplicate_user_id(self):
        """测试重复学号"""
        print("\n运行 test_register_with_duplicate_user_id")
        # 先创建一个用户
        User.objects.create_user(
            email='another@example.com',
            password=self.valid_payload['password'],
            user_id=self.valid_payload['user_id'],
            name='另一个用户',
            school='北京大学',
            role='STUDENT'
        )

        # 尝试用相同的学号注册
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('已存在', response.data['message'])

    def test_register_with_invalid_email(self):
        """测试无效邮箱格式"""
        print("\n运行 test_register_with_invalid_email")
        payload = self.valid_payload.copy()
        payload['email'] = 'invalid-email'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '请输入合法的邮件地址。')

    def test_register_with_short_password(self):
        """测试密码过短"""
        print("\n运行 test_register_with_short_password")
        payload = self.valid_payload.copy()
        payload['password'] = '12345'  # 5个字符
        payload['confirm_password'] = '12345'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '密码长度不能少于6个字符')

    def test_register_with_long_password(self):
        """测试密码过长"""
        print("\n运行 test_register_with_long_password")
        payload = self.valid_payload.copy()
        payload['password'] = 'a' * 21  # 21个字符
        payload['confirm_password'] = 'a' * 21
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], '密码长度不能超过20个字符')

    def test_register_with_valid_password_length(self):
        """测试有效密码长度"""
        print("\n运行 test_register_with_valid_password_length")
        payload = self.valid_payload.copy()
        payload['password'] = '123456'  # 6个字符
        payload['confirm_password'] = '123456'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_admin_role(self):
        """测试注册ADMIN角色"""
        print("\n运行 test_register_admin_role")
        payload = self.valid_payload.copy()
        payload['role'] = 'ADMIN'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], '不允许注册管理员角色')

    def test_register_teacher_role_without_token(self):
        """测试未登录用户注册TEACHER角色"""
        print("\n运行 test_register_teacher_role_without_token")
        payload = self.valid_payload.copy()
        payload['role'] = 'TEACHER'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], '未提供有效的访问令牌或令牌已过期')
        
    def test_register_teacher_role_with_admin(self):
        """测试管理员注册TEACHER角色"""
        print("\n运行 test_register_teacher_role_with_admin")
        # 使用setUpClass中创建的管理员用户
        self.client.force_authenticate(user=self.admin)
        
        payload = self.valid_payload.copy()
        payload['role'] = 'TEACHER'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], '注册成功')
        
        # 验证用户是否创建成功
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.role, 'TEACHER') 