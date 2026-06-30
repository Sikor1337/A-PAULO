export type UserStatus = 'new_volunteer' | 'regular' | 'admin';

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  status: UserStatus;
  is_active: boolean;
}

export interface AdminUserInput {
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  status: UserStatus;
  is_active: boolean;
  password?: string;
}
