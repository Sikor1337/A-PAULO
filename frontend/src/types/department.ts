export interface DepartmentListItem {
  id: number;
  name: string;
  icon: string;
  description: string;
  is_archived: boolean;
  member_count: number;
}

export interface DepartmentMember {
  id: number;
  volunteer_id: number;
  full_name: string;
  email: string;
  status: string;
  created_at: string;
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
