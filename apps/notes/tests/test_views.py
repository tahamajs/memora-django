from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.notes.models import Note, Category

User = get_user_model()

class NoteAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass123')
        self.client.force_login(self.user)
        self.category = Category.objects.create(name='Work')

    def test_create_note(self):
        url = reverse('note-list')   # adjust name if needed
        data = {'title': 'New Note', 'content': 'Hello', 'category': self.category.id}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.count(), 1)

    def test_list_notes(self):
        Note.objects.create(title='Note 1', content='Content 1', author=self.user)
        url = reverse('note-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)