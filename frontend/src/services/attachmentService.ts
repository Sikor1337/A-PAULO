import apiClient from '@/lib/api';
import type { AttachmentUpdateInput, BOCardAttachment, BOCardUploadInput } from '@/types';

export const BO_CARD_ACCEPT = 'application/pdf,image/jpeg,image/png,image/webp,image/heic,image/heif,.pdf,.jpg,.jpeg,.png,.webp,.heic,.heif';
export const BO_CARD_MAX_SIZE_BYTES = 10 * 1024 * 1024;
export const BO_CARD_SUPPORTED_LABEL = 'PDF, JPG, PNG, WEBP, HEIC/HEIF do 10 MB';

export const attachmentService = {
  listBOCards: async (groupId: number): Promise<BOCardAttachment[]> => {
    const response = await apiClient.get<BOCardAttachment[]>('v1/attachments/bo-cards', {
      params: { group_id: groupId, limit: 1000 },
    });
    return response.data;
  },

  uploadBOCard: async ({ groupId, beneficiaryId, volunteerId, period, file }: BOCardUploadInput): Promise<BOCardAttachment> => {
    const form = new FormData();
    form.append('content', file);
    form.append('group_id', String(groupId));
    form.append('beneficiary_id', String(beneficiaryId));
    form.append('volunteer_id', String(volunteerId));
    form.append('period', period);

    const response = await apiClient.post<BOCardAttachment>('v1/attachments/bo-cards', form);
    return response.data;
  },

  update: async (id: number, data: AttachmentUpdateInput): Promise<BOCardAttachment> => {
    const response = await apiClient.patch<BOCardAttachment>(`v1/attachments/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`v1/attachments/${id}`);
  },

  openContent: async (attachment: BOCardAttachment): Promise<void> => {
    const previewWindow = window.open('about:blank', '_blank');
    if (previewWindow) {
      previewWindow.opener = null;
      previewWindow.document.title = attachment.display_name;
    }

    try {
      const response = await apiClient.get(`v1/attachments/${attachment.id}/content`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: attachment.content_type });
      const url = URL.createObjectURL(blob);
      if (previewWindow) {
        previewWindow.location.href = url;
      } else {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (error) {
      previewWindow?.close();
      throw error;
    }
  },
};
