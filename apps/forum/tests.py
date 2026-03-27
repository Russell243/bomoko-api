from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from forum.models import ForumPost

User = get_user_model()


class ForumModerationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='forum-user', password='StrongPass123')
        self.other = User.objects.create_user(username='forum-other', password='StrongPass123')
        self.client.force_authenticate(user=self.user)

    def test_post_with_blocked_keyword_is_marked_blocked(self):
        payload = {
            'title': 'Sujet critique',
            'content': 'Cas de pornographie dans le campus',
            'is_anonymous': True,
        }
        response = self.client.post('/api/forum/posts/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['moderation_status'], ForumPost.MODERATION_BLOCKED)

    def test_post_with_flagged_keyword_is_marked_flagged(self):
        payload = {
            'title': 'Besoin aide',
            'content': 'Je subis du harcelement en cours',
            'is_anonymous': True,
        }
        response = self.client.post('/api/forum/posts/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['moderation_status'], ForumPost.MODERATION_FLAGGED)

    def test_list_hides_blocked_posts_from_other_users(self):
        blocked = ForumPost.objects.create(
            user=self.user,
            title='Bloque',
            content='porn',
            moderation_status=ForumPost.MODERATION_BLOCKED,
            moderation_reason='mot_interdit:porn',
        )
        approved = ForumPost.objects.create(
            user=self.user,
            title='OK',
            content='contenu normal',
            moderation_status=ForumPost.MODERATION_APPROVED,
        )

        self.client.force_authenticate(user=self.other)
        response = self.client.get('/api/forum/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(approved.id), ids)
        self.assertNotIn(str(blocked.id), ids)

    def test_like_increments_post_counter(self):
        post = ForumPost.objects.create(
            user=self.user,
            title='Post aime',
            content='contenu normal',
            moderation_status=ForumPost.MODERATION_APPROVED,
        )

        response = self.client.post(f'/api/forum/posts/{post.id}/like/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post.refresh_from_db()
        self.assertEqual(post.likes_count, 1)
        self.assertEqual(response.data['likes_count'], 1)

    def test_reply_increments_counter_only_for_non_blocked_reply(self):
        post = ForumPost.objects.create(
            user=self.user,
            title='Post discussion',
            content='contenu normal',
            moderation_status=ForumPost.MODERATION_APPROVED,
        )

        response = self.client.post(
            f'/api/forum/posts/{post.id}/reply/',
            {'content': 'Je confirme cette situation.', 'is_anonymous': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post.refresh_from_db()
        self.assertEqual(post.replies_count, 1)
