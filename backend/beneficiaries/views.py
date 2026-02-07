from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Beneficiary
from .serializers import BeneficiarySerializer
from .filters import BeneficiaryFilter


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Beneficiary model.
    Provides CRUD operations with filtering, searching and ordering.
    """
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = BeneficiaryFilter
    search_fields = ['full_name', 'address']
    ordering_fields = '__all__'
    ordering = ['full_name']
