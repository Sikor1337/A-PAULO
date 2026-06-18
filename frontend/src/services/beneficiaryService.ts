import { createCrudService } from './crudService';
import type { Beneficiary, BeneficiaryInput } from '@/types';

export const beneficiaryService = createCrudService<Beneficiary, BeneficiaryInput>('v1/beneficiaries');
