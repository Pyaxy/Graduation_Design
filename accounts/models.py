from operator import attrgetter
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models.functions.datetime import TruncMinute
from django.utils import choices, module_loading

# Create your models here.


class CustomUserManager(BaseUserManager):
    """
    UserManger to create user and super_user.
    """

    # define create_user
    def create_user(self, user_id, email, name, school, role, password=None):
        if not email:
            raise ValueError("请填写邮箱作为登录的唯一凭证")
        user = self.model(
            user_id=user_id,
            email=self.normalize_email(email=email),
            name=name,
            school=school,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    # define create_superuser
    def create_superuser(self, user_id, email, name, school, password, **extra_fields):
        extra_fields.setdefault("role", "ADMIN")
        user = self.create_user(
            user_id=user_id,
            email=email,
            name=name,
            school=school,
            role=extra_fields["role"],
            password=password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ("STUDENT", "学生"),
        ("TEACHER", "教师"),
        ("ADMIN", "管理员"),
    )

    user_id = models.CharField(
        primary_key=True, max_length=20, verbose_name="学号/工号"
    )
    email = models.EmailField(unique=True, verbose_name="邮箱")
    name = models.CharField(max_length=50, verbose_name="姓名")
    school = models.CharField(max_length=100, verbose_name="学校")
    role = models.CharField(
        max_length=10,
        choices=ROLES,
        default="STUDENT",
        verbose_name="角色",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    is_staff = models.BooleanField(default=False, verbose_name="是否是管理员")

    USERNAME_FIELD = "email"  # 使用邮箱登录
    # 创建用户时要求的字段
    REQUIRED_FIELDS = ["user_id", "name", "school", "role"]

    objects = CustomUserManager()  # 将自定义的用户管理器与之绑定

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"
