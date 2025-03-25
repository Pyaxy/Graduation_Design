from django.urls import path

from .api import views

urlpatterns = [
    # path("login/", views.RoleLoginView.as_view(), name="login"),
    # path("welcome/", views.RoleWelcomeView.as_view(), name="role_welcome"),
    path("api/v1/accounts/login/", views.LoginView.as_view(), name="login"),
    path(
        "api/v1/accounts/refresh/",
        views.CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("api/v1/accounts/user/", views.current_user, name="user"),
]
