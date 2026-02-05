from django.db import models
from django.contrib.auth.models import AbstractUser

class UserProfile(AbstractUser):

    STATUS = (
        ('regular', 'regular'),
        ('admin', 'admin')
    )

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=30, choices=STATUS, default='regular')


    def __str__(self):
        return self.username
