import { createCrudService } from './crudService';
import type { Role, RoleInput } from '@/types';

export const roleService = createCrudService<Role, RoleInput>('v1/roles');
