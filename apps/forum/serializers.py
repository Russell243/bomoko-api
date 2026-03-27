from rest_framework import serializers
from django.db.models import Q
from .models import ForumCategory, ForumPost, ForumReply


class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = '__all__'


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ForumReply
        fields = '__all__'
        read_only_fields = ('post', 'user', 'created_at', 'moderation_status', 'moderation_reason', 'moderated_at')

    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Anonyme"
        return obj.user.username


class ForumPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = '__all__'
        read_only_fields = (
            'user',
            'likes_count',
            'replies_count',
            'created_at',
            'updated_at',
            'moderation_status',
            'moderation_reason',
            'moderated_at',
        )

    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Anonyme"
        return obj.user.username

    def get_replies(self, obj):
        request = self.context.get('request')
        qs = obj.replies.all()

        if request and request.user and request.user.is_authenticated and not request.user.is_staff:
            qs = qs.filter(
                Q(moderation_status=ForumReply.MODERATION_APPROVED) |
                Q(user=request.user)
            )

        return ForumReplySerializer(qs, many=True, context=self.context).data


class ForumPostListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list view (no replies)."""
    author_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = ForumPost
        exclude = ('user',)
        read_only_fields = (
            'likes_count',
            'replies_count',
            'created_at',
            'updated_at',
            'moderation_status',
            'moderation_reason',
            'moderated_at',
        )

    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Anonyme"
        return obj.user.username
