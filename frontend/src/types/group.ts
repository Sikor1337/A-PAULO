/** Group as returned in list views by GroupSerializer (backend/groups/serializers.py). */
export interface GroupListItem {
  id: number;
  name: string;
  leader: number | null;
  leader_name: string | null;
  beneficiary_count: number;
  volunteer_count: number;
}

/** A volunteer nested under a beneficiary in a group detail (BeneficiaryInGroupSerializer.get_volunteers). */
export interface AssignmentVolunteer {
  id: number;
  full_name: string;
  assignment_id: number;
  is_main: boolean;
  additional_info: string;
}

/** A beneficiary nested in a group detail (BeneficiaryInGroupSerializer). */
export interface GroupBeneficiary {
  id: number;
  full_name: string;
  phone: string | null;
  address: string;
  status: string;
  volunteers: AssignmentVolunteer[];
}

/** Full group detail (GET /v1/groups/:id/). */
export interface GroupDetail extends GroupListItem {
  beneficiaries: GroupBeneficiary[];
}

/** One volunteer entry inside a mass-assignment payload. */
export interface AssignmentVolunteerInput {
  id: number;
  additional_info: string;
}

/** One beneficiary's assignment inside a mass-assignment payload. */
export interface AssignmentInput {
  beneficiary: number;
  volunteers: AssignmentVolunteerInput[];
  main_volunteer: number | null;
}

/** Writable payload for creating/updating a group with mass assignments. */
export interface GroupSaveInput {
  name: string;
  leader: number | null;
  assignments: AssignmentInput[];
}

/** Assignment row (BeneficiaryAssignmentSerializer) — used by the assignments endpoint. */
export interface BeneficiaryAssignment {
  id: number;
  beneficiary: number;
  volunteer: number;
  volunteer_name: string;
  beneficiary_name: string;
  is_main: boolean;
  additional_info: string;
  created_at: string;
}
