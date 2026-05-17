from rest_framework import serializers
from .models import Volunteer


class VolunteerSerializer(serializers.ModelSerializer):
    """Serializer for Volunteer model"""
    
    led_group = serializers.SerializerMethodField()
    assigned_groups = serializers.SerializerMethodField()

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
            'led_group',
            'assigned_groups',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'led_group', 'assigned_groups']
    
    def get_led_group(self, obj):
        group = obj.led_groups.first()
        return group.name if group else None

    def get_assigned_groups(self, obj):
        return ", ".join(obj.assigned_groups.values_list('name', flat=True))
    
    def validate_phone(self, value):
        """Validate phone number format"""
        import re
        if value and not re.match(r'^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$', value):
            raise serializers.ValidationError("Podaj prawidłowy polski numer telefonu (np. +48 123 456 789)")
        return value
