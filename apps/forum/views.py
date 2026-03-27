from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, Q
from django.utils import timezone
from .models import ForumCategory, ForumPost, ForumReply
from .moderation import moderate_forum_text
from .serializers import (
    ForumCategorySerializer, ForumPostSerializer,
    ForumPostListSerializer, ForumReplySerializer
)


class ForumCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ForumCategorySerializer
    queryset = ForumCategory.objects.all()


class ForumPostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ForumPostListSerializer
        return ForumPostSerializer

    def get_queryset(self):
        queryset = ForumPost.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(moderation_status=ForumPost.MODERATION_APPROVED) |
                Q(user=self.request.user)
            )
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset

    def perform_create(self, serializer):
        title = serializer.validated_data.get('title', '')
        content = serializer.validated_data.get('content', '')
        status_value, reason = moderate_forum_text(f"{title}\n{content}")
        serializer.save(
            user=self.request.user,
            moderation_status=status_value,
            moderation_reason=reason,
            moderated_at=timezone.now(),
        )

    def perform_update(self, serializer):
        title = serializer.validated_data.get('title', serializer.instance.title)
        content = serializer.validated_data.get('content', serializer.instance.content)
        status_value, reason = moderate_forum_text(f"{title}\n{content}")
        serializer.save(
            moderation_status=status_value,
            moderation_reason=reason,
            moderated_at=timezone.now(),
        )

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        post = self.get_object()
        serializer = ForumReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply_content = serializer.validated_data.get('content', '')
        status_value, reason = moderate_forum_text(reply_content)
        serializer.save(
            user=request.user,
            post=post,
            moderation_status=status_value,
            moderation_reason=reason,
            moderated_at=timezone.now(),
        )
        if status_value != ForumReply.MODERATION_BLOCKED:
            ForumPost.objects.filter(id=post.id).update(replies_count=F('replies_count') + 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        ForumPost.objects.filter(id=post.id).update(likes_count=F('likes_count') + 1)
        post.refresh_from_db(fields=['likes_count'])
        return Response({'likes_count': post.likes_count})
