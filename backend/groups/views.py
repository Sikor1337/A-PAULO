from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count
from .models import Group, BeneficiaryAssignment
from .serializers import GroupSerializer, BeneficiaryAssignmentSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Group model.
    Provides CRUD operations for groups, including mass assignment of beneficiaries and volunteers.
    """
    permission_classes = [AllowAny] # Keeping AllowAny as per user request for dev
    serializer_class = GroupSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        return Group.objects.select_related('leader').annotate(
            beneficiary_count=Count('beneficiaries', distinct=True),
            volunteer_count=Count('volunteers', distinct=True),
        ).prefetch_related(
            'volunteers',
            'beneficiaries__volunteer_assignments__volunteer'
        )


class BeneficiaryAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing volunteer-beneficiary assignments.
    """
    queryset = BeneficiaryAssignment.objects.select_related('beneficiary', 'volunteer').all()
    serializer_class = BeneficiaryAssignmentSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering = ['beneficiary__full_name']
