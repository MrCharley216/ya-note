from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):
    """Класс тестирования логики."""
    NEW_TEXT = 'Изменённый текст.'

    @classmethod
    def setUpTestData(cls):
        """метод класса для фикстур."""
        cls.auth_user = User.objects.create(username='Пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.auth_user)
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.success_url = reverse('notes:success')
        cls.note_url = reverse('notes:detail', args=(cls.note.id,))
        cls.add_url = reverse('notes:add', None)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse(
            'notes:delete',
            args=(cls.note.slug,)
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': cls.NEW_TEXT,
            'slug': 'new_slug'
        }

    def test_anonymous_user_cant_create_note(self):
        """Поверка недоступности создания заметки анонимом."""
        self.client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_auth_user_can_create_note(self):
        """
        Проверка доступности создания заметки
        авторизованным пользователем.
        """
        self.user_client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)

    def test_unique_slug(self):
        """Проверка уникальности slug."""
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(self.note.slug + WARNING))
        assert Note.objects.count() == 1

    def test_empty_slug(self):
        """Тест создания заметки без slug."""
        form_data = self.form_data.copy()
        form_data.pop('slug')
        url = reverse('notes:add')
        response = self.author_client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.last()
        expected_slug = slugify(form_data['title'])
        print(expected_slug)
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_delete_note(self):
        """Поверка удаления заметки автором."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Проверка невозможности удаления чужой заметки."""
        response = self.user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_user_cant_edit_note_of_another_user(self):
        """Проверка невозможности редактирования чужой заметки."""
        response = self.user_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_author_can_edit_note(self):
        """Проверка доступности редактирования заметки автором."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_TEXT)
