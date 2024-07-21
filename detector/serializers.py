from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .utils import detect_points_of_interest
import cv2
import numpy as np
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
# from rest_framework.authtoken.models import Token


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ImageProcessingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image = cv2.imdecode(np.frombuffer(serializer.validated_data['image'].read(), np.uint8), cv2.IMREAD_COLOR)
            points = detect_points_of_interest(image)
            return Response({'points': points})
        return Response(serializer.errors, status=400)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid Credentials")
