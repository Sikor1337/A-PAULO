from django.db import models


class Group(models.Model):
    """Model representing a volunteer group for beneficiary care."""

    name = models.CharField(max_length=100, verbose_name="Nazwa grupy")
    leader = models.ForeignKey(
        'volunteers.Volunteer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_groups',
        verbose_name="Lider grupy"
    )
    volunteers = models.ManyToManyField(
        'volunteers.Volunteer',
        blank=True,
        related_name='assigned_groups',
        verbose_name="Wolontariusze w grupie"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    class Meta:
        ordering = ['name']
        verbose_name = "Grupa"
        verbose_name_plural = "Grupy"

    def __str__(self):
        return self.name


class BeneficiaryAssignment(models.Model):
    """Assignment of a volunteer to a beneficiary (many-to-many through table)."""

    beneficiary = models.ForeignKey(
        'beneficiaries.Beneficiary',
        on_delete=models.CASCADE,
        related_name='volunteer_assignments',
        verbose_name="Podopieczny"
    )
    volunteer = models.ForeignKey(
        'volunteers.Volunteer',
        on_delete=models.CASCADE,
        related_name='beneficiary_assignments',
        verbose_name="Wolontariusz"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data przypisania")

    class Meta:
        unique_together = ['beneficiary', 'volunteer']
        ordering = ['beneficiary__full_name']
        verbose_name = "Przypisanie"
        verbose_name_plural = "Przypisania"

    def __str__(self):
        return f"{self.volunteer} → {self.beneficiary}"
