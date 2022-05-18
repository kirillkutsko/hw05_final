from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page_url(self):
        """Проверить доступность URL."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_error_page_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
