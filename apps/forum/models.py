import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ForumCategory(models.Model):
    """Topic categories for the community forum."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='chatbubbles-outline')

    class Meta:
        verbose_name_plural = 'Forum Categories'

    def __str__(self):
        return self.name


class ForumPost(models.Model):
    """Community discussion post — supports anonymous posting for safety."""
    MODERATION_APPROVED = 'approved'
    MODERATION_FLAGGED = 'flagged'
    MODERATION_BLOCKED = 'blocked'
    MODERATION_STATUS_CHOICES = (
        (MODERATION_APPROVED, 'Approved'),
        (MODERATION_FLAGGED, 'Flagged'),
        (MODERATION_BLOCKED, 'Blocked'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    category = models.ForeignKey(ForumCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)

    likes_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default=MODERATION_APPROVED,
    )
    moderation_reason = models.CharField(max_length=255, blank=True, default='')
    moderated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        author = "Anonyme" if self.is_anonymous else str(self.user)
        return f"{self.title} by {author}"


class ForumReply(models.Model):
    """Reply to a forum post."""
    MODERATION_APPROVED = 'approved'
    MODERATION_FLAGGED = 'flagged'
    MODERATION_BLOCKED = 'blocked'
    MODERATION_STATUS_CHOICES = (
        (MODERATION_APPROVED, 'Approved'),
        (MODERATION_FLAGGED, 'Flagged'),
        (MODERATION_BLOCKED, 'Blocked'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_replies')
    content = models.TextField()
    is_anonymous = models.BooleanField(default=True)
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default=MODERATION_APPROVED,
    )
    moderation_reason = models.CharField(max_length=255, blank=True, default='')
    moderated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply to {self.post.title}"
