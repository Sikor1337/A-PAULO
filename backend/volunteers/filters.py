import django_filters
from .models import Volunteer


class VolunteerFilter(django_filters.FilterSet):
    """Filter for Volunteer model"""
    
    full_name = django_filters.CharFilter(lookup_expr='icontains', label='Imię i Nazwisko')
    email = django_filters.CharFilter(lookup_expr='icontains', label='Email')
    status = django_filters.ChoiceFilter(choices=Volunteer.STATUS_CHOICES, label='Status')
    
    class Meta:
        model = Volunteer
        fields = [
            'full_name', 'email', 'status'
        ]
