from django.contrib import admin
from .models import Beneficiary


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    """Admin interface for Beneficiary model"""
    
    list_display = ['full_name', 'status', 'bo_enrolled', 'phone', 'created_at']
    list_filter = ['status', 'bo_enrolled', 'created_at']
    search_fields = ['full_name', 'address', 'phone', 'family_phone']
    ordering = ['full_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('full_name', 'address', 'phone', 'family_phone', 'description')
        }),
        ('Status i uczestnictwo', {
            'fields': ('status', 'bo_enrolled')
        }),
        ('Daty', {
            'fields': ('last_priest_visit', 'last_volunteer_meeting')
        }),
        ('Dodatkowe informacje', {
            'fields': ('history',)
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
