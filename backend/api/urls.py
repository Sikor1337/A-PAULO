from django.urls import path, include
from . import views


urlpatterns = [
    path('items/', views.ItemListCreateView.as_view(), name='item-list-create'),
]
