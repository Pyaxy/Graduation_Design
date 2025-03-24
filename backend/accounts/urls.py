from django.urls import path

from .api import views

urlpatterns = [
    # path("login/", views.RoleLoginView.as_view(), name="login"),
    # path("welcome/", views.RoleWelcomeView.as_view(), name="role_welcome"),
    path("login/", views.LoginView.as_view(), name="login")
]
