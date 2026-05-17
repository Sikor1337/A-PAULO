from rest_framework import serializers
from .models import Beneficiary


class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for Beneficiary model"""
    group_name = serializers.CharField(source='group.name', read_only=True, default=None)

    class Meta:
        model = Beneficiary
        fields = [
            'id',
            'full_name',
            'address',
            'phone',
            'family_phone',
            'description',
            'group',
            'group_name',
            'status',
            'bo_enrolled',
            'last_priest_visit',
            'last_volunteer_meeting',
            'history',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_phone(self, value):
        """Validate phone number format"""
        import re
        if value and not re.match(r'^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$', value):
            raise serializers.ValidationError("Podaj prawidłowy polski numer telefonu (np. +48 123 456 789)")
        return value
    
    def validate_family_phone(self, value):
        """Validate family phone number format"""
        import re
        if value and not re.match(r'^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$', value):
            raise serializers.ValidationError("Podaj prawidłowy polski numer telefonu (np. +48 123 456 789)")
        return value
