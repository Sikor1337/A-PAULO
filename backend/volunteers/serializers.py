from rest_framework import serializers
from .models import Volunteer


class VolunteerSerializer(serializers.ModelSerializer):
    """Serializer for Volunteer model"""
    
    class Meta:
        model = Volunteer
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'social_link',
            'status',
            'join_date',
            'notes',
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
