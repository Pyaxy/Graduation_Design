from django.urls import path, include
from rest_framework.routers import DefaultRouter
from subject.api.views import SubjectViewSet, PublicSubjectViewSet

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'public-subjects', PublicSubjectViewSet, basename='public-subject')

urlpatterns = [
    path('api/v1/', include(router.urls)),
] 