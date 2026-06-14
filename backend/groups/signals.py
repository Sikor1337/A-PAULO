from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Group, BeneficiaryAssignment


@receiver(pre_delete, sender=Group)
def clear_orphaned_assignments(sender, instance, **kwargs):
    """
    When a group is deleted, its beneficiaries are detached (Beneficiary.group is
    SET_NULL). BeneficiaryAssignment has no FK to the group, so its rows would
    otherwise linger and keep pointing at now group-less beneficiaries. Remove
    the assignments belonging to this group's beneficiaries.
    """
    BeneficiaryAssignment.objects.filter(beneficiary__group=instance).delete()
