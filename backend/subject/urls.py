from django.urls import path, include
from rest_framework.routers import DefaultRouter
from subject.api.views import SubjectViewSet

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')

urlpatterns = [
    path('api/v1/', include(router.urls)),
] 