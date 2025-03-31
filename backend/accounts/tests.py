from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User

class LoginViewTestCase(APITestCase):
    """登录测试接口"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            user_id="testuserID",
            email="testuser@example.com",
            password="testpassword",
            name="Test User",
            role="user",
            school="testschool",
        )

    def test_login_success(self):
        """测试登录成功"""
        url = reverse("login")
        data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        # 发送登录请求
        response = self.client.post(url, data, format="json")
        # 断言响应状态码为200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertIn("user_id", response.data["data"])
        self.assertIn("role", response.data["data"])
        self.assertIn("name", response.data["data"])
        # 断言响应消息
        self.assertEqual(response.data["message"], "登录成功")

    def test_login_invalid_credentials(self):
        """测试登录密码错误"""
        url = reverse("login")
        data = {
            "email": "testuser@example.com",
            "password": "wrongpassword"
        }
        # 发送登录请求
        response = self.client.post(url, data, format="json")
        # 断言响应状态码为401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 断言响应数据结构
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["message"], "找不到指定凭据对应的有效用户")
    
    def test_login_missing_password(self):
        """测试登录缺少密码"""
        url = reverse("login")
        data = {
            "email": "testuser@example.com"
        }
        # 发送登录请求
        response = self.client.post(url, data, format="json")
        # 断言响应状态码为400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 断言响应数据结构
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["message"], "密码不能为空")

    def test_login_missing_email(self):
        """测试登录缺少邮箱"""
        url = reverse("login")
        data = {
            "password": "testpassword"
        }
        # 发送登录请求
        response = self.client.post(url, data, format="json")
        # 断言响应状态码为400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 断言响应数据结构
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["message"], "邮箱不能为空")

    def test_login_missing_email_and_password(self):
        """测试登录缺少邮箱和密码"""
        url = reverse("login")
        data = {}
        # 发送登录请求
        response = self.client.post(url, data, format="json")
        # 断言响应状态码为400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 断言响应数据结构
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["message"], "邮箱和密码不能为空")

class TokenRefreshViewTestCase(APITestCase):
    """刷新令牌测试接口"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            user_id="testuserID",
            email="testuser@example.com",
            password="testpassword",
            name="Test User",
            role="user",
            school="testschool",
        )
        # 通过登录接口获取刷新令牌
        login_url = reverse("login")
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post(login_url, login_data, format="json")
        self.refresh_token = login_response.data["data"]["refresh"]
        self.access_token = login_response.data["data"]["access"]
        self.refresh_url = reverse("token_refresh")

    def test_refresh_token_success(self):
        """测试成功刷新令牌"""
        data = {
            "refresh": self.refresh_token
        }
        response = self.client.post(self.refresh_url, data, format="json")
        
        # 断言响应状态码为200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应消息
        self.assertEqual(response.data["message"], "刷新令牌成功")
        # 断言响应数据内容
        self.assertIn("access", response.data["data"])
        self.assertIn("user_id", response.data["data"])
        self.assertIn("role", response.data["data"])
        self.assertIn("name", response.data["data"])

    def test_refresh_token_invalid(self):
        """测试使用无效的刷新令牌"""
        data = {
            "refresh": "a_invalid_token"
        }
        response = self.client.post(self.refresh_url, data, format="json")
        
        # 断言响应状态码为401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["data"], None)
        self.assertEqual(response.data["message"], "无效的刷新令牌")

    def test_refresh_token_missing(self):
        """测试未提供刷新令牌"""
        data = {}
        response = self.client.post(self.refresh_url, data, format="json")
        
        # 断言响应状态码为400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["data"], None)
        self.assertEqual(response.data["message"], "刷新令牌不能为空")

class CurrentUserViewTestCase(APITestCase):
    """获取当前用户信息测试接口"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            user_id="testuserID",
            email="testuser@example.com",
            password="testpassword",
            name="Test User",
            role="user",
            school="testschool",
        )
        # 获取访问令牌
        login_url = reverse("login")
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post(login_url, login_data, format="json")
        self.access_token = login_response.data["data"]["access"]
        self.current_user_url = reverse("current_user")

    def test_get_current_user_success(self):
        """测试成功获取当前用户信息"""
        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        # 发送请求
        response = self.client.get(self.current_user_url)
        
        # 断言响应状态码为200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应消息
        self.assertEqual(response.data["message"], "获取用户信息成功")
        # 断言响应数据内容
        self.assertEqual(response.data["data"]["user_id"], "testuserID")
        self.assertEqual(response.data["data"]["name"], "Test User")
        self.assertEqual(response.data["data"]["role"], "user")

    def test_get_current_user_unauthorized(self):
        """测试未认证获取当前用户信息"""
        # 不设置认证头
        response = self.client.get(self.current_user_url)
        
        # 断言响应状态码为401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["data"], None)
        self.assertEqual(response.data["message"], "未提供有效的访问令牌或令牌已过期")
    def test_get_current_user_invalid_token(self):
        """测试使用无效的令牌获取当前用户信息"""
        # 设置无效的认证头
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        # 发送请求
        response = self.client.get(self.current_user_url)
        
        # 断言响应状态码为401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 断言响应数据结构
        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        # 断言响应数据内容
        self.assertEqual(response.data["data"], None)
        self.assertEqual(response.data["message"], "未提供有效的访问令牌或令牌已过期")
        