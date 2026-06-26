export interface BOCardAttachment {
  id: number;
  context: 'bo_card';
  group_id: number | null;
  beneficiary_id: number | null;
  volunteer_id: number | null;
  period: string | null;
  display_name: string;
  description: string;
  original_filename: string;
  storage_backend: string;
  content_type: string;
  size_bytes: number;
  checksum_sha256: string;
  created_by_id: number | null;
  created_by_username: string | null;
  updated_by_id: number | null;
  updated_by_username: string | null;
  created_at: string;
  updated_at: string;
}

export interface BOCardUploadInput {
  groupId: number;
  beneficiaryId: number;
  volunteerId: number;
  period: string;
  file: File;
}

export interface AttachmentUpdateInput {
  display_name?: string;
  description?: string;
}

export type BOCardSortKey =
  | 'created_at'
  | 'updated_at'
  | 'period'
  | 'display_name'
  | 'group_name'
  | 'beneficiary_name'
  | 'volunteer_name'
  | 'size_bytes';

export type SortDirection = 'asc' | 'desc';

export interface BOCardOverviewAttachment extends BOCardAttachment {
  group_name: string | null;
  beneficiary_name: string | null;
  volunteer_name: string | null;
}

export interface BOCardOverviewResponse {
  items: BOCardOverviewAttachment[];
  total: number;
  skip: number;
  limit: number;
}

export interface BOCardOverviewFilters {
  search?: string;
  groupId?: number | '';
  beneficiaryId?: number | '';
  volunteerId?: number | '';
  periodFrom?: string;
  periodTo?: string;
  hasComment?: '' | 'yes' | 'no';
  sortBy?: BOCardSortKey;
  sortDirection?: SortDirection;
  page?: number;
  limit?: number;
}
