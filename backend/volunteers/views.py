from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Volunteer
from .serializers import VolunteerSerializer
from .filters import VolunteerFilter


class VolunteerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Volunteer model.
    Provides CRUD operations with filtering, searching and ordering.
    """
    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = VolunteerFilter
    search_fields = ['full_name', 'email']
    ordering_fields = '__all__'
    ordering = ['full_name']
