from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .apis.views import CourseViewSet, GroupViewSet, GroupCodeVersionViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'groups/(?P<group_pk>[^/.]+)/versions', GroupCodeVersionViewSet, basename='group-version')
urlpatterns = [
    path('api/v1/', include(router.urls)),
] 