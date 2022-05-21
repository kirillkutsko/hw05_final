import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import POST_PER_PAGE

from ..forms import CommentForm
from ..models import Comment, Follow, Group, Post

User = get_user_model()
POSTS = 13
SECOND_PAGE_POSTS = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoNameAuthor')
        cls.user_follower = User.objects.create_user(username='Follower')
        cls.user_following = User.objects.create_user(username='Following')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.index = reverse('posts:index')
        cls.group_list = reverse('posts:group_posts', kwargs={
            'slug': 'test_slug'
        })
        cls.profile = reverse('posts:profile', kwargs={
            'username': 'NoNameAuthor'
        })
        cls.post_detail = reverse('posts:post_detail', kwargs={'post_id': '1'})
        cls.post_create = reverse('posts:post_create')
        cls.post_edit = reverse('posts:post_edit', kwargs={'post_id': '1'})
        cls.follow_index = reverse('posts:follow_index')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.post_to_follow = Post.objects.create(
            author=cls.user_following,
            text='Пост для проверки подписок',
        )
        cls.true_group = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.post.author
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_follower_client = Client()
        self.user_follower_client.force_login(self.user_follower)
        self.user_following_client = Client()
        self.user_following_client.force_login(self.user_following)
        cache.clear()

    def test_index_correct_context(self):
        """Проверить контекст шаблона index."""
        response = self.authorized_client.get(self.index)
        self.assertEqual(response.context['post'], self.post)

    def test_group_posts_correct_context(self):
        """Проверить контекст шаблона group_posts."""
        response = self.authorized_client.get(self.group_list)
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['group'], self.group)

    def test_profile_correct_context(self):
        """Проверить контекст шаблона profile."""
        response = self.authorized_client.get(self.profile)
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['author'], self.user)
        self.assertTrue(response.context['following'], self.follow)

    def test_post_detail_correct_context(self):
        """Проверить контекст шаблона post_detail."""
        response = self.authorized_client.get(self.post_detail)
        self.assertEqual(response.context['post'], self.post)
        self.assertTrue(response.context['comments'], self.comment)
        self.assertTrue(response.context['form'], CommentForm())

    def test_follow_index_correct_context(self):
        """Проверить контекст шаблона follow_index."""
        response = self.authorized_client.get(self.follow_index)
        self.assertEqual(response.context['post'], self.post)

    def test_post_edit_correct_context(self):
        """Проверить контекст шаблона post_edit."""
        form_fields = [
            (
                'text',
                forms.fields.CharField,
                self.authorized_client.get(self.post_edit)
            ),
            (
                'group',
                forms.fields.ChoiceField,
                self.authorized_client.get(self.post_edit)
            ),
            (
                'image',
                forms.fields.ImageField,
                self.authorized_client.get(self.post_edit)
            ),
            (
                'text',
                forms.fields.CharField,
                self.authorized_client.get(self.post_create)
            ),
            (
                'group',
                forms.fields.ChoiceField,
                self.authorized_client.get(self.post_create)
            ),
            (
                'image',
                forms.fields.ImageField,
                self.authorized_client.get(self.post_create)
            )
        ]
        for value, expected, response in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_true_group(self):
        """
        Проверить правильность группы у поста.
        """
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    args=[self.true_group.slug]))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_add_posts_comment(self):
        """
        Проверить добавление комментария.
        """
        comment_count = Comment.objects.count()
        new_comment = {
            'text': 'text-test'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=new_comment,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий',
                author=self.user,
            ).exists()
        )

    def test_guest_client_cant_comment(self):
        """
        Не авторизованный пользователь не может комментировать.
        """
        comment_count = Comment.objects.count()
        new_comment = {
            'text': 'text-test'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=new_comment,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )

    def test_cache_index(self):
        """Проверить кэш главной страницы."""
        post_1 = Post.objects.create(
            author=self.user,
            text='Тестовый пост_1',
            group=self.group
        )
        response_1 = self.authorized_client.get(self.index)
        Post.objects.filter(pk=post_1.id).delete()
        response_2 = self.authorized_client.get(self.index)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(self.index)
        self.assertNotEqual(response_2.content, response_3.content)

    def test_follow(self):
        """Проверить подписку на автора."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.user_follower_client.get(self.follow_index)
        self.assertEqual(
            response.context['page_obj'][0].text,
            self.post_to_follow.text
        )
        response_2 = self.user_following_client.get(self.follow_index)
        self.assertNotEqual(response_2, self.post_to_follow.text)

    def test_unfollow(self):
        """Проверить отмену подписки на автора."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.user_follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following}
            )
        )
        follow = None
        self.assertEqual(response.context, follow)

    def test_new_post_in_follow_user(self):
        """
        Проверить новые посты пользователей у подписчиков.
        """
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.user_follower_client.get(self.follow_index)
        self.assertEqual(
            response.context['page_obj'][0].text,
            self.post_to_follow.text
        )

    def test_new_post_in_ufollow_user(self):
        """
        Проверить новые посты пользователей у не подписчиков.
        """
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.user_following_client.get(self.follow_index)
        self.assertNotEqual(
            response.context,
            self.post_to_follow
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author = Client()
        cls.author = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='test_title',
            description='test_description',
            slug='test-slug'
        )
        cache.clear()

    def setUp(self):
        for post_temp in range(POSTS):
            Post.objects.create(
                text=f'text{post_temp}', author=self.author, group=self.group
            )

    def test_first_page_contains_ten_records(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_posts.html':
                reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': self.author}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), POST_PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index') + '?page=2',
            'posts/group_posts.html':
                reverse('posts:group_posts',
                        kwargs={'slug': self.group.slug}) + '?page=2',
            'posts/profile.html':
                reverse('posts:profile',
                        kwargs={'username': self.author}) + '?page=2',
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(
                    response.context['page_obj']), SECOND_PAGE_POSTS
                )
