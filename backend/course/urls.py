from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis.views import CourseViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
] 