import json
import random

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.admin import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class CreateTableAPITest(APITestCase):
    def setUp(self) -> None:
        self.valid_table_data = {
            "name": "good_name",
            "fields": [
                {"type": "string", "title": "good_name"},
                {"type": "number", "title": "age"},
                {"type": "boolean", "title": "is_active"}
            ]
        }
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_create_table_valid(self):
        url = reverse('table-api')
        response = self.client.post(url, self.valid_table_data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_table_already_exists(self):
        url = reverse('table-api')

        response = self.client.post(url, self.valid_table_data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, self.valid_table_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_create_table_with_invalid_field_type(self):
        url = reverse('table-api')
        data = {"title": "good_name", 'fields': [{'type': 'invalid', 'name': 'field_name_too_long'}]}
        response = self.client.post(url, data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['fields']['0']['type'][0], '"invalid" is not a valid choice.')

    def test_create_table_with_field_name_too_long(self):
        url = reverse('table-api')
        data = {"title": "good_name", 'fields': [{'type': 'string', 'title': 'field_name_too_long' * 100}]}
        response = self.client.post(url, data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['fields']['0']['title'][0], 'Ensure this field has no more than 100 characters.')

    def test_create_table_with_field_name_too_short(self):
        url = reverse('table-api')
        data = {"name": "good_name", 'fields': [{'type': 'string', 'title': 'n1'}]}
        response = self.client.post(url, data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['fields']['0']['title'][0], 'Ensure this field has at least 3 characters.')

    def test_create_table_required_fields(self):
        url = reverse('table-api')
        data = {"name_": "good_name", 'fields': [{'type': 'string'}]}
        response = self.client.post(url, data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['name'][0], 'This field is required.')
        self.assertEqual(res_data['fields']['0']['title'][0], 'This field is required.')

    def test_create_table_fields_max_allowed(self):
        url = reverse('table-api')
        fields = [{'type': 'string', 'title': f'field_{i}'} for i in range(11)]
        data = {"name": "good_name", 'fields': fields}
        response = self.client.post(url, data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['fields'][0], 'Maximum of 10 fields allowed.')


class UpdateTableAPITest(APITestCase):
    def setUp(self) -> None:
        self.valid_table_data = {
            "name": "update_table_test",
            "fields": [
                {"type": "string", "title": "good_name"},
                {"type": "number", "title": "age"},
                {"type": "boolean", "title": "is_active"}
            ]
        }
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_update_table_add_field(self):
        url = reverse('table-api')
        response = self.client.post(url, self.valid_table_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        table_name = "update_table_test"
        updated_table_data = {
            "name": table_name,
            "fields": [
                {"type": "string", "title": "good_name"},
                {"type": "number", "title": "age"},
                {"type": "boolean", "title": "is_active"},
                {"type": "string", "title": "new_field"}
            ]
        }
        url = reverse('table-api-detail', kwargs={'id': table_name})
        response = self.client.put(url, updated_table_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_table_remove_field(self):
        url = reverse('table-api')
        table_name = "update_table_remove_field_test"

        response = self.client.post(url, {**self.valid_table_data, 'name': table_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        updated_table_data = {
            "name": table_name,
            "fields": [
                {"type": "string", "title": "good_name"},
                {"type": "number", "title": "age"},
            ]
        }
        url = reverse('table-api-detail', kwargs={'id': table_name})
        response = self.client.put(url, updated_table_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_table_change_field_type_not_allowed(self):
        url = reverse('table-api')
        table_name = "update_table_remove_field_test"

        response = self.client.post(url, {**self.valid_table_data, 'name': table_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        updated_table_data = {
            "name": table_name,
            "fields": [
                {"type": "string", "title": "good_name"},
                {"type": "string", "title": "age"},
                {"type": "string", "title": "is_active"},
                {"type": "string", "title": "new_field"}
            ]
        }
        url = reverse('table-api-detail', kwargs={'id': table_name})
        response = self.client.put(url, updated_table_data, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data[0], 'Changing field type not allowed.')


class TableRowGetAPITest(APITestCase):
    def setUp(self) -> None:
        self.table_name = "gym_subscribers1"
        self.valid_table_data = {
            "name": self.table_name,
            "fields": [
                {"type": "string", "title": "name"},
                {"type": "number", "title": "age"},
                {"type": "boolean", "title": "is_active"}
            ]
        }
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        url = reverse('table-api')
        self.client.post(url, self.valid_table_data, format='json')
        url = reverse('table-row-api', kwargs={'id': self.table_name})
        for i in range(1, 6):
            self.client.post(url, {
                'name': f'Gym User {i}',
                'age': random.randint(1, 150),
                'is_active': False
            }, format='json')

    def test_table_row_get(self):
        url = reverse('table-row-api', kwargs={'id': self.table_name})

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)
        self.assertEqual(len(res_data), 5)


class TableRowAddAPITest(APITestCase):
    def setUp(self) -> None:
        self.table_name = "gym_subscribers2"
        self.valid_table_data = {
            "name": self.table_name,
            "fields": [
                {"type": "string", "title": "name"},
                {"type": "number", "title": "age"},
                {"type": "boolean", "title": "is_active"}
            ]
        }
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        url = reverse('table-api')
        self.client.post(url, self.valid_table_data, format='json')

    def test_table_row_add_valid_fields(self):
        url = reverse('table-row-api', kwargs={'id': self.table_name})

        response = self.client.post(url, {
            'name': 'Gym User 1',
            'age': 12,
            'is_active': False
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_table_row_add_field_not_found(self):
        url = reverse('table-row-api', kwargs={'id': self.table_name})

        response = self.client.post(url, {
            'name': 'Gym User 1',
            'age': 12,
            'is_active': False,
            'field_not_found': 'n/a'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_table_row_add_required_field(self):
        url = reverse('table-row-api', kwargs={'id': self.table_name})

        response = self.client.post(url, {
            'name': 'Gym User 1',
            'age': 12,
        }, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['is_active'][0], 'This field is required.')

    def test_table_row_add_invalid_field_type(self):
        url = reverse('table-row-api', kwargs={'id': self.table_name})

        response = self.client.post(url, {
            'name': 'Gym User 1',
            'age': 'invalid_number',
        }, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data['age'][0], 'A valid integer is required.')

    def test_table_row_add_max_rows_exceeded(self):
        url = reverse('table-row-api', kwargs={'id': self.table_name})
        for _ in range(20):
            response = self.client.post(url, {
                'name': 'Gym User 1',
                'age': 12,
                'is_active': False
            }, format='json')
        res_data = json.loads(response.content.decode('utf-8'))
        print(res_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data[0], 'Exceeded max rows allowed.')
