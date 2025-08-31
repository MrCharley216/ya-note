from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты для маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """Загрузка данных для тестирования."""
        cls.author = User.objects.create(username='Лев Толстой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.reader = User.objects.create(username='Читатель простой')

    def test_anon_homepage_availability(self):
        """
        Тест доступа анонима к главной
        странице и страницам входа/регистрации.
        """
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_author(self):
        """Тест для проверки доступа автора."""
        self.client.force_login(self.author)
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,))
        )

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_auth_user(self):
        """Тест для проверки доступа аутентифицированного пользователя."""
        self.client.force_login(self.reader)
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None)
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """Тест для редиректа на страницу логина."""
        for name in ('notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.id,))
                redirect_url = f'{reverse('users:login')}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_succes_url_after_edit(self):
        """Тест редиректа после успешного редактирования заметки."""
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, {
            "title": 'Новый заголовок',
            "text": 'Новый текст'
        })
        self.assertRedirects(response, reverse('notes:success'))

    def test_pages_availability_for_authenticated_reader(self):
        """
        Тест доступности страниц для авторизованного
        пользователя (не автора).
        """
        self.client.force_login(self.reader)
        public_urls = (
            ('notes:list', None),
            ('notes:add', None),
        )
        for name, args in public_urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        protected_urls = (
            ('notes:edit', (self.note.id,)),
            ('notes:delete', (self.note.id,)),
            ('notes:detail', (self.note.id,)),
        )
        for name, args in protected_urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn(response.status_code, [
                    HTTPStatus.NOT_FOUND,
                    HTTPStatus.FORBIDDEN
                ])
    