from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForumCategoryViewSet, ForumPostViewSet

app_name = 'forum'

router = DefaultRouter()
router.register('categories', ForumCategoryViewSet, basename='forum-category')
router.register('posts', ForumPostViewSet, basename='forum-post')

urlpatterns = [
    path('', include(router.urls)),
]
