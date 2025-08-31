from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestHomePage(TestCase):
    """Тест для отображения заметок на главной странице."""

    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        """Создание объектов."""
        cls.author = User.objects.create(username='Автор заметок')
        all_notes = [
            Note(
                title=f'Заметка {index}',
                text='Просто текст.',
                author=cls.author,
                slug=f'slug-{index}'
            )
            for index in range(settings.COUNT_NOTES_ON_LIST_PAGE + 1)
        ]
        
        Note.objects.bulk_create(all_notes)

    def test_content_list_page(self):
        """Проверка списка заметок."""
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        self.assertIn("object_list", response.context)
        notes = response.context["object_list"]
        self.assertEqual(
            list(notes),
            list(Note.objects.filter(author=self.author))
        )

    def test_form_add_edit_page(self):
        """
        Проверка передачи формы на страницы
        создания и редактирования заметки.
        """
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (Note.objects.first().slug,))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
