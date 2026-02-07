from django.contrib import admin
from .models import Volunteer


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    """Admin interface for Volunteer model"""
    
    list_display = ['full_name', 'email', 'status', 'phone', 'join_date']
    list_filter = [
        'status', 'join_date'
    ]
    search_fields = ['full_name', 'email', 'phone']
    ordering = ['full_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('full_name', 'email', 'phone', 'social_link')
        }),
        ('Status i daty', {
            'fields': ('status', 'join_date')
        }),
        ('Dodatkowe informacje', {
            'fields': ('notes', 'history')
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
