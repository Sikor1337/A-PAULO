import { createCrudService } from './crudService';
import type { VolunteerFunction, VolunteerFunctionInput } from '@/types';

export const functionService = createCrudService<VolunteerFunction, VolunteerFunctionInput>('v1/functions');
