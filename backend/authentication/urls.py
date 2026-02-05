from django.urls import path, include
from . import views
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='get_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('user/', views.CurrentUserView.as_view(), name='current_user'),
    
]
