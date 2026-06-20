import { createCrudService } from './crudService';
import type { AdminUser, AdminUserInput } from '@/types';

export const userService = createCrudService<AdminUser, AdminUserInput>('v1/users');
