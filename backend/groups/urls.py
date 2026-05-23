from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, BeneficiaryAssignmentViewSet

# Explicitly defining paths to avoid conflict between 'assignments' string and group 'pk'
urlpatterns = [
    # Assignments first
    path('assignments/', BeneficiaryAssignmentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='assignment-list'),
    path('assignments/<int:pk>/', BeneficiaryAssignmentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='assignment-detail'),
    
    # Groups second
    path('', GroupViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='group-list'),
    path('<int:pk>/', GroupViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='group-detail'),
]
