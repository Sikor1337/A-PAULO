import django_filters
from .models import Beneficiary


class BeneficiaryFilter(django_filters.FilterSet):
    """Filter for Beneficiary model"""
    
    full_name = django_filters.CharFilter(lookup_expr='icontains', label='Imię i Nazwisko')
    status = django_filters.ChoiceFilter(choices=Beneficiary.STATUS_CHOICES, label='Status')
    bo_enrolled = django_filters.BooleanFilter(label='Uczestnik BO')
    
    class Meta:
        model = Beneficiary
        fields = ['full_name', 'status', 'bo_enrolled']
