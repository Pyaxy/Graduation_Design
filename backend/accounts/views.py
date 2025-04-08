from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from accounts.forms import RoleBasedLoginForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
# Create your views here.


class RoleLoginView(LoginView):
    form_class = RoleBasedLoginForm
    template_name = "accounts/login.html"

    # 登录后跳转
    def get_success_url(self):
        return reverse_lazy("role_welcome")


class RoleWelcomeView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/welcome.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.request.user.get_role_display()
        return context
