import { createCrudService } from './crudService';
import type { Volunteer, VolunteerInput } from '@/types';

export const volunteerService = createCrudService<Volunteer, VolunteerInput>('v1/volunteers/');
