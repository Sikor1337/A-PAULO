from rest_framework import serializers
from .models import Beneficiary


class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for Beneficiary model"""
    
    class Meta:
        model = Beneficiary
        fields = [
            'id',
            'full_name',
            'address',
            'phone',
            'family_phone',
            'description',
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
        if value and not value.replace(' ', '').replace('+', '').replace('-', '').isdigit():
            raise serializers.ValidationError("Phone number can only contain digits, spaces, + and -")
        return value
    
    def validate_family_phone(self, value):
        """Validate family phone number format"""
        if value and not value.replace(' ', '').replace('+', '').replace('-', '').isdigit():
            raise serializers.ValidationError("Phone number can only contain digits, spaces, + and -")
        return value
