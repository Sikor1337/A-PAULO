export interface BOCardAttachment {
  id: number;
  context: 'bo_card';
  group_id: number;
  beneficiary_id: number;
  volunteer_id: number;
  period: string;
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
