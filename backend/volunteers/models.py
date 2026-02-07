from django.db import models


class Volunteer(models.Model):
    """Model representing a volunteer."""
    
    STATUS_CHOICES = [
        ('Aktywny', 'Aktywny'),
        ('Były', 'Były'),
    ]
    
    # Basic Information
    full_name = models.CharField(max_length=200, verbose_name="Imię i Nazwisko")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    social_link = models.URLField(blank=True, null=True, verbose_name="Link do profilu społecznościowego")
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aktywny', verbose_name="Status")
    join_date = models.DateField(verbose_name="Data przystąpienia")
        
    # Additional Information
    notes = models.TextField(blank=True, verbose_name="Notatki")
    history = models.TextField(blank=True, verbose_name="Historia")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")
    
    class Meta:
        ordering = ['full_name']
        verbose_name = "Wolontariusz"
        verbose_name_plural = "Wolontariusze"
    
    def __str__(self):
        return self.full_name
