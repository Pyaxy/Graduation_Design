from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.RoleLoginView.as_view(), name="login"),
    path("welcome/", views.RoleWelcomeView.as_view(), name="role_welcome"),
]
