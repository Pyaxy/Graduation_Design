from django import forms
from django.contrib.auth.forms import AuthenticationForm


class RoleBasedLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="登录邮箱", widget=forms.EmailInput(attrs={"autofocus": True})
    )
    password = forms.CharField(label="密码", strip=False, widget=forms.PasswordInput)
    error_messages = {
        "invalid_login": "邮箱或密码错误",
        "inactive": "该账号已被停用",
    }
