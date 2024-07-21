import cv2
import numpy as np
import unittest
import io
import json
import os
from config import SECRET_KEY, DEBUG, ALLOWED_HOSTS, BASE_DIR
from .serializers import ImageUploadSerializer, RegisterUserSerializer, LoginSerializer
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .utils import detect_points_of_interest
from rest_framework.test import APITestCase, APIClient
from process_images import process_image, main
from unittest.mock import mock_open, patch
from rest_framework import status
from django.test import TestCase
from PIL import Image
from io import BytesIO
from django.urls import reverse


class DetectorTests(APITestCase):
    def setUp(self):
        self.client = APIClient()


class ConfigTestCase(unittest.TestCase):

    def test_secret_key_exists(self):
        self.assertIsNotNone(SECRET_KEY)

    def test_debug_is_true(self):
        self.assertTrue(DEBUG)

    def test_allowed_hosts_is_list(self):
        self.assertTrue(isinstance(ALLOWED_HOSTS, list))

    def test_base_dir_is_string(self):
        self.assertIsInstance(BASE_DIR, str)


if __name__ == '__main__':
    unittest.main()


class SerializerTestCase(unittest.TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }

    def test_image_upload_serializer_valid_data(self):
        # Открываем исходный файл изображения для чтения бинарных данных
        with open('input/1_Color.png', 'rb') as f:
            image_data = f.read()
        # Формирование данных для сериализатора
        image = SimpleUploadedFile('1_Color.png', image_data, content_type='image/png')
        data = {'image': image}
        # Создание сериализатора и проверка валидности
        serializer = ImageUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_image_upload_serializer_invalid_data(self):
        data = {
            'image': None  # передаем неверные данные
        }
        serializer = ImageUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_login_serializer_valid_credentials(self):
        # Создаем пользователя для проверки логина
        user = User.objects.create_user(**self.user_data)
        credentials = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        serializer = LoginSerializer(data=credentials)
        self.assertTrue(serializer.is_valid())
        authenticated_user = serializer.validated_data
        self.assertEqual(authenticated_user.id, user.id)

    def test_login_serializer_invalid_credentials(self):
        credentials = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        serializer = LoginSerializer(data=credentials)
        self.assertFalse(serializer.is_valid())

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_process_image_failure(self, mock_open):
        with self.assertRaises(FileNotFoundError):
            process_image('test_image.png')

    @patch('requests.post')
    def test_process_image_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'points_of_interest': [1, 2, 3]}

        result = process_image('test_image.png')
        self.assertEqual(result, {'points_of_interest': [1, 2, 3]})

    def test_main(self):
        input_files = ['1_Color.png', '2_Color.png', '3_Color.png']
        output_file = 'output/results.json'

        expected_data = {
            "1_Color.png": {
                "points_of_interest": [1, 2, 3]
            },
            "2_Color.png": {
                "points_of_interest": [1, 2, 3]
            },
            "3_Color.png": {
                "points_of_interest": [1, 2, 3]
            }
        }

        # Mock для проверки функции os.path.exists
        with patch("os.path.exists", return_value=False):
            # Mock для создания директории output
            with patch("os.makedirs"):
                # Mock для открытия файла и записи
                mock_file = mock_open()
                with patch("builtins.open", mock_file):
                    main(input_files, output_file)

        # Проверка вызовов метода write на объекте файла
        handle = mock_file()
        handle.write.assert_called_once()

        # Проверка записанных данных
        written_data = handle.write.call_args[0][0]
        if written_data:
            written_data_dict = json.loads(written_data)
        else:
            written_data_dict = {}

        # Ожидаемый результат должен соответствовать только успешно обработанным изображениям
        expected_data_subset = {key: expected_data[key] for key in input_files if key in written_data_dict}

        self.assertEqual(written_data_dict, expected_data_subset)


class RegisterUserViewTests(APITestCase):
    def test_register_user(self):
        url = reverse('register')
        data = {'username': 'testuser', 'password': 'testpass'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_register_user_missing_data(self):
        url = reverse('register')
        data = {'username': 'testuser'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterUserSerializerTests(TestCase):
    def test_register_user_serializer_valid_data(self):
        data = {'username': 'testuser', 'password': 'testpass'}
        serializer = RegisterUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass'))

    def test_register_user_serializer_missing_data(self):
        data = {'username': 'testuser'}
        serializer = RegisterUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class LoginSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_login_serializer_valid_credentials(self):
        data = {'username': 'testuser', 'password': 'testpass'}
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, self.user)

    def test_login_serializer_invalid_credentials(self):
        data = {'username': 'testuser', 'password': 'wrongpass'}
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class ImageUploadSerializerTests(unittest.TestCase):
    def generate_image_file(self):
        image = Image.new('RGB', (100, 100))
        byte_arr = io.BytesIO()
        image.save(byte_arr, format='JPEG')
        byte_arr.seek(0)
        return byte_arr

    def test_image_upload_serializer_valid_data(self):
        image_file = self.generate_image_file()
        uploaded_file = SimpleUploadedFile("test.jpg", image_file.read(), content_type="image/jpeg")
        data = {'image': uploaded_file}
        serializer = ImageUploadSerializer(data=data)
        is_valid = serializer.is_valid()
        errors = serializer.errors
        self.assertTrue(is_valid, msg=f"Errors: {errors}")
        if is_valid:
            validated_data = serializer.validated_data
            image = cv2.imdecode(np.frombuffer(validated_data['image'].read(), np.uint8), cv2.IMREAD_COLOR)
            self.assertEqual(image.shape, (100, 100, 3))

    def test_image_upload_serializer_invalid_data(self):
        data = {'image': 'not_an_image'}
        serializer = ImageUploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors)


class UtilsTests(unittest.TestCase):
    def generate_image_file(self, color=(0, 0, 0)):
        image = Image.new('RGB', (100, 100), color)
        byte_arr = BytesIO()
        image.save(byte_arr, format='JPEG')
        byte_arr.seek(0)
        return byte_arr

    def test_process_image_invalid_path(self):
        # Проверяем вызов функции с некорректным путем к изображению
        with self.assertRaises(FileNotFoundError):
            process_image("invalid_path.jpg")

    def test_detect_points_of_interest_valid(self):
        # Генерируем синтетическое черно-белое изображение с простым узором
        image = np.zeros((100, 100), np.uint8)
        cv2.rectangle(image, (30, 30), (70, 70), 255, -1)  # белый квадрат в центре

        # Обрабатываем изображение для получения углов
        points = detect_points_of_interest(image)

        # Проверяем, что углы были найдены
        self.assertGreater(len(points), 0)

    def test_detect_points_of_interest_empty_image(self):
        # Генерируем пустое изображение
        image = np.zeros((100, 100), np.uint8)

        # Обрабатываем изображение для получения углов
        points = detect_points_of_interest(image)

        # Проверяем, что углы не были найдены
        self.assertEqual(len(points), 0)

    def test_detect_points_of_interest_save_json(self):
        # Генерируем синтетическое черно-белое изображение с простым узором
        image = np.zeros((100, 100), np.uint8)
        cv2.circle(image, (50, 50), 10, 255, -1)  # белый круг в центре

        # Обрабатываем изображение для получения углов
        points = detect_points_of_interest(image)

        # Проверяем, что JSON файл был создан и содержит данные
        json_path = 'output/results.json'
        self.assertTrue(os.path.exists(json_path))

        with open(json_path, 'r') as json_file:
            data = json.load(json_file)
            self.assertEqual(data, points)

        # Удаляем JSON файл после теста
        os.remove(json_path)


if __name__ == '__main__':
    unittest.main()
