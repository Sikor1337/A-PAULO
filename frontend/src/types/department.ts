export interface DepartmentListItem {
  id: number;
  name: string;
  icon: string;
  description: string;
  is_archived: boolean;
  member_count: number;
}

export type MembershipStatus = 'PENDING' | 'ACTIVE';

export interface DepartmentMember {
  id: number;
  volunteer_id: number;
  full_name: string;
  email: string;
  status: string;
  membership_status: MembershipStatus;
  created_at: string;
}

export interface DepartmentInventoryItem {
  id: number;
  department_id: number;
  name: string;
  location: string;
  borrowed_by_volunteer_id: number | null;
  borrowed_by_volunteer_name: string | null;
  borrowed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DepartmentInventoryItemInput {
  name: string;
  location: string;
  borrowed_by_volunteer_id: number | null;
  borrowed_at: string | null;
}

export interface DepartmentDetail {
  id: number;
  name: string;
  icon: string;
  description: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  members: DepartmentMember[];
}

export interface DepartmentInput {
  name: string;
  icon: string;
  description: string;
}
