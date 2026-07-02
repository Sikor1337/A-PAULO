export type PermissionCode =
  | 'CAN_VIEW_USERS'
  | 'CAN_MANAGE_USERS'
  | 'CAN_VIEW_VOLUNTEERS'
  | 'CAN_MANAGE_VOLUNTEERS'
  | 'CAN_VIEW_BENEFICIARIES'
  | 'CAN_MANAGE_BENEFICIARIES'
  | 'CAN_VIEW_PI_GROUPS'
  | 'CAN_MANAGE_PI_GROUPS'
  | 'CAN_VIEW_FUNCTIONS'
  | 'CAN_MANAGE_FUNCTIONS'
  | 'CAN_VIEW_ATTACHMENTS'
  | 'CAN_MANAGE_ATTACHMENTS'
  | 'CAN_VIEW_RECRUITMENT'
  | 'CAN_MANAGE_RECRUITMENT'
  | 'CAN_VIEW_EVENTS'
  | 'CAN_MANAGE_EVENTS'
  | 'CAN_VIEW_SECURITY'
  | 'CAN_MANAGE_SECURITY';

export interface SecurityPermission {
  id: number;
  code: PermissionCode;
  name: string;
  category: string;
}

export interface SecurityGroup {
  id: number;
  name: string;
  description: string;
  is_system: boolean;
  system_key: string | null;
  permissions: SecurityPermission[];
  user_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface SecurityGroupInput {
  name: string;
  description: string;
  permission_codes: PermissionCode[];
}

export interface SecurityGroupSaveInput extends SecurityGroupInput {
  user_ids: number[];
}

export interface MyPermissions {
  permissions: PermissionCode[];
  group_ids: number[];
}
