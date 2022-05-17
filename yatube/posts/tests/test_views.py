import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
POSTS = 13
SECOND_PAGE_POSTS = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POST_PER_PAGE = 10


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cls.user = User.objects.create_user(username='NoNameAuthor')
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
        cls.post_edit = reverse('posts:post_edit', kwargs={'post_id': '1'})
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
        cls.true_group = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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

    def test_post_detail_correct_context(self):
        """Проверить контекст шаблона post_detail."""
        response = self.authorized_client.get(self.post_detail)
        self.assertEqual(response.context['post'], self.post)

    def test_create_post_edit_correct_context(self):
        """Проверить контекст шаблона post_edit при редактировании."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        response = self.authorized_client.get(self.post_edit)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        """Проверить контекст шаблона post_edit при создании."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in form_fields.items():
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

    def test_guest_client_cant_comment(self):
        """
        Не авторизованный пользователь не может комментировать.
        """
        comment_count = Comment.objects.count()
        new_comment = {
            'text': 'text-test'
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=new_comment,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)


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
