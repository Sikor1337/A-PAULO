from django.db import models


class Beneficiary(models.Model):
    """Model representing a beneficiary."""
    
    STATUS_CHOICES = [
        ('OBECNY', 'Obecny'),
        ('ZMARŁY', 'Zmarły'),
        ('BYŁY', 'Były'),
        ('DPS_ZOL', 'DPS/ZOL'),
    ]
    
    # Basic Information
    full_name = models.CharField(max_length=200, verbose_name="Imię i Nazwisko")
    address = models.TextField(verbose_name="Adres")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon podopiecznego")
    family_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon rodziny/opiekuna")
    description = models.TextField(blank=True, verbose_name="Opis podopiecznego")
    
    # Status Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OBECNY', verbose_name="Status")
    bo_enrolled = models.BooleanField(default=False, verbose_name="Uczestnik BO")
    
    # Dates
    last_priest_visit = models.DateField(null=True, blank=True, verbose_name="Data ostatnich odwiedzin księdza")
    last_volunteer_meeting = models.DateField(null=True, blank=True, verbose_name="Termin ostatniego spotkania z wolontariuszami")
    
    # Additional Info
    history = models.TextField(blank=True, verbose_name="Historia")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    
    class Meta:
        ordering = ['full_name']
        verbose_name = "Podopieczny"
        verbose_name_plural = "Podopieczni"
    
    def __str__(self):
        return self.full_name
