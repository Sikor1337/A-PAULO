import apiClient from '@/lib/api';
import type {
  MyPermissions,
  PermissionCode,
  SecurityGroup,
  SecurityGroupInput,
  SecurityGroupSaveInput,
  SecurityPermission,
} from '@/types';

const base = 'v1/security';

export const permissionService = {
  getMine: async (): Promise<MyPermissions> => {
    const response = await apiClient.get<MyPermissions>(`${base}/me/permissions`);
    return response.data;
  },
  getPermissions: async (): Promise<SecurityPermission[]> => {
    const response = await apiClient.get<SecurityPermission[]>(`${base}/permissions`);
    return response.data;
  },
  getGroups: async (): Promise<SecurityGroup[]> => {
    const response = await apiClient.get<SecurityGroup[]>(`${base}/groups`);
    return response.data;
  },
  createGroup: async (input: SecurityGroupInput): Promise<SecurityGroup> => {
    const response = await apiClient.post<SecurityGroup>(`${base}/groups`, input);
    return response.data;
  },
  updateGroup: async (
    id: number,
    input: Pick<SecurityGroupInput, 'name' | 'description'>,
  ): Promise<SecurityGroup> => {
    const response = await apiClient.patch<SecurityGroup>(`${base}/groups/${id}`, input);
    return response.data;
  },
  saveGroup: async (id: number, input: SecurityGroupSaveInput): Promise<SecurityGroup> => {
    const response = await apiClient.put<SecurityGroup>(`${base}/groups/${id}`, input);
    return response.data;
  },
  setGroupPermissions: async (
    id: number,
    permissionCodes: PermissionCode[],
  ): Promise<SecurityGroup> => {
    const response = await apiClient.put<SecurityGroup>(`${base}/groups/${id}/permissions`, {
      permission_codes: permissionCodes,
    });
    return response.data;
  },
  setGroupUsers: async (id: number, userIds: number[]): Promise<SecurityGroup> => {
    const response = await apiClient.put<SecurityGroup>(`${base}/groups/${id}/users`, {
      user_ids: userIds,
    });
    return response.data;
  },
  deleteGroup: async (id: number): Promise<void> => {
    await apiClient.delete(`${base}/groups/${id}`);
  },
  getUserGroups: async (userId: number): Promise<number[]> => {
    const response = await apiClient.get<number[]>(`${base}/users/${userId}/groups`);
    return response.data;
  },
  setUserGroups: async (userId: number, groupIds: number[]): Promise<number[]> => {
    const response = await apiClient.put<number[]>(`${base}/users/${userId}/groups`, {
      group_ids: groupIds,
    });
    return response.data;
  },
};
