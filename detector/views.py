from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
import tempfile
from .utils import process_image, detect_points_of_interest
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
import json
import os
import numpy as np
from .serializers import RegisterUserSerializer


# Создадим эндпоинты для регистрации и получения токенов
class RegisterUserView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ObtainTokenView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            # Создаем токен доступа
            access_token = AccessToken.for_user(user)
            return Response({'token': str(access_token)}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class ImageProcessingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                self.serialize_response({"error": "No image provided"}),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохраняем загруженное изображение во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_file.read())
            temp_file_path = temp_file.name

        try:
            gray_image = process_image(temp_file_path)
            points_of_interest = detect_points_of_interest(gray_image)
            return Response(
                self.serialize_response({"points_of_interest": points_of_interest}),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                self.serialize_response({"error": str(e)}),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Удаляем временный файл после обработки
            os.remove(temp_file_path)

    def serialize_response(self, data):
        """
        Сериализует данные в JSON строку с компактным форматом, обрабатывая нестандартные типы данных.
        """
        def default_serializer(obj):
            if isinstance(obj, (np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
                return int(obj)
            if isinstance(obj, np.float32) or isinstance(obj, np.float64):
                return float(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        return json.dumps(data, default=default_serializer, ensure_ascii=False, separators=(',', ':'))


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @staticmethod
    def get_token(user):
        token = super().get_token(user)

        # Добавьте дополнительные данные в токен
        token['username'] = user.username
        token['email'] = user.email

        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Можно добавить дополнительные данные в ответ
        return data


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
