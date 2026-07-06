"""Audit state snapshots for PI domain entities."""

from app.core.audit import audit_value
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import Group, BeneficiaryAssignment
from app.modules.pi.models.volunteer import Volunteer


def volunteer_audit_state(volunteer: Volunteer) -> dict:
	"""Capture volunteer state for audit comparison."""
	return {
		"full_name": audit_value(volunteer.full_name),
		"email": audit_value(volunteer.email),
		"phone": audit_value(volunteer.phone),
		"social_link": audit_value(volunteer.social_link),
		"status": audit_value(volunteer.status),
		"join_date": audit_value(volunteer.join_date),
		"notes": audit_value(volunteer.notes),
	}


def beneficiary_audit_state(beneficiary: Beneficiary) -> dict:
	"""Capture beneficiary state for audit comparison."""
	return {
		"full_name": audit_value(beneficiary.full_name),
		"address": audit_value(beneficiary.address),
		"phone": audit_value(beneficiary.phone),
		"family_phone": audit_value(beneficiary.family_phone),
		"description": audit_value(beneficiary.description),
		"group_id": audit_value(beneficiary.group_id),
		"status": audit_value(beneficiary.status),
		"bo_enrolled": audit_value(beneficiary.bo_enrolled),
		"last_priest_visit": audit_value(beneficiary.last_priest_visit),
		"last_volunteer_meeting": audit_value(beneficiary.last_volunteer_meeting),
	}


def group_audit_state(group: Group) -> dict:
	"""Capture group state for audit comparison."""
	return {
		"name": audit_value(group.name),
		"leader_id": audit_value(getattr(group, "leader_id", None)),
	}


def assignment_audit_state(assignment: BeneficiaryAssignment) -> dict:
	"""Capture assignment state for audit comparison."""
	return {
		"beneficiary_id": audit_value(assignment.beneficiary_id),
		"volunteer_id": audit_value(assignment.volunteer_id),
		"is_main": audit_value(assignment.is_main),
		"additional_info": audit_value(assignment.additional_info),
	}
