export type BeneficiaryStatus = 'OBECNY' | 'ZMARŁY' | 'BYŁY' | 'DPS_ZOL';

/** Beneficiary as returned by BeneficiarySerializer (backend/beneficiaries/serializers.py). */
export interface Beneficiary {
  id: number;
  full_name: string;
  address: string;
  phone: string;
  family_phone: string;
  description: string | null;
  group: number | null;
  group_name: string | null;
  status: BeneficiaryStatus;
  bo_enrolled: boolean;
  last_priest_visit: string | null;
  last_volunteer_meeting: string | null;
  history: string | null;
  created_at: string;
  updated_at: string;
}

/** Writable payload for creating/updating a beneficiary. */
export interface BeneficiaryInput {
  full_name: string;
  address: string;
  phone: string;
  family_phone: string;
  description?: string;
  group?: number | null;
  status: BeneficiaryStatus;
  bo_enrolled: boolean;
  last_priest_visit?: string | null;
  last_volunteer_meeting?: string | null;
  history?: string;
}
