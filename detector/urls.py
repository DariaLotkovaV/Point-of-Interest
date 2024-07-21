from django.urls import path
from .views import ImageProcessingView, RegisterUserView, ObtainTokenView, CustomTokenRefreshView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('token/', ObtainTokenView.as_view(), name='token'),
    path('process-image/', ImageProcessingView.as_view(), name='image_processing_view'),
    path('detect/', ImageProcessingView.as_view(), name='detect_points_of_interest'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
