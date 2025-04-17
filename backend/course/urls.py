from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis.views import CourseViewSet, GroupViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'groups', GroupViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
] 