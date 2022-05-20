from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_not_author = User.objects.create_user(username='auth_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост п',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_url_for_authorized_client(self):
        """
        Доступность url адресов для авторизованного пользователя
        """
        test_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=[self.user.username]
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in test_urls.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template(self):
        """
        URL-адрес использует соответствующий шаблон.
        """
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_posts', kwargs={'slug': 'test_slug'}),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': f'{self.user}'}),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{self.post.id}'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template_user(self):
        """URL-адрес использует соответствующий шаблон для auth_users"""
        templates_pages_names = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_pages_redirects(self):
        """Проверить редиректы неавторизованного пользователя."""
        templates_pages_names = {
            reverse('posts:post_create'): '/auth/login/?next=/create/',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): f'/auth/login/?next=/posts/{self.post.id}/edit/',
            reverse('posts:follow_index'): '/auth/login/?next=/follow/'
        }
        for reverse_name, redirect in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertRedirects(response, redirect)

    def test_404_page(self):
        """
        Запрос к несуществующей странице
        """
        response = self.guest_client.get('/unknown/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """
        Проверить редирект авторизированого не автора поста
        со страницы редактирования поста.
        """
        response = self.authorized_client_not_author.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )
