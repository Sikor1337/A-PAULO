import apiClient from '@/lib/api';
import type {
  AttachmentUpdateInput,
  BOCardAttachment,
  BOCardOverviewFilters,
  BOCardOverviewResponse,
  BOCardUploadInput,
} from '@/types';

export const BO_CARD_ACCEPT = 'application/pdf,image/jpeg,image/png,image/webp,image/heic,image/heif,.pdf,.jpg,.jpeg,.png,.webp,.heic,.heif';
export const BO_CARD_MAX_SIZE_BYTES = 10 * 1024 * 1024;
export const BO_CARD_SUPPORTED_LABEL = 'PDF, JPG, PNG, WEBP, HEIC/HEIF do 10 MB';

const compactParams = (params: Record<string, string | number | boolean | undefined>) =>
  Object.fromEntries(Object.entries(params).filter(([, value]) => value !== undefined && value !== ''));

const overviewParams = (filters: BOCardOverviewFilters, includePaging = true) => {
  const limit = filters.limit ?? 25;
  const page = Math.max(1, filters.page ?? 1);
  return compactParams({
    search: filters.search?.trim(),
    group_id: filters.groupId,
    beneficiary_id: filters.beneficiaryId,
    volunteer_id: filters.volunteerId,
    period_from: filters.periodFrom,
    period_to: filters.periodTo,
    has_comment: filters.hasComment === 'yes' ? true : filters.hasComment === 'no' ? false : undefined,
    sort_by: includePaging ? (filters.sortBy ?? 'created_at') : undefined,
    sort_direction: includePaging ? (filters.sortDirection ?? 'desc') : undefined,
    skip: includePaging ? (page - 1) * limit : undefined,
    limit: includePaging ? limit : undefined,
  });
};

const filenameFromDisposition = (disposition: string | undefined) => {
  const match = disposition?.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? 'karty-bo.zip';
};

export const attachmentService = {
  listBOCards: async (groupId: number): Promise<BOCardAttachment[]> => {
    const response = await apiClient.get<BOCardAttachment[]>('v1/attachments/bo-cards', {
      params: { group_id: groupId, limit: 1000 },
    });
    return response.data;
  },

  listBOCardsOverview: async (filters: BOCardOverviewFilters): Promise<BOCardOverviewResponse> => {
    const response = await apiClient.get<BOCardOverviewResponse>('v1/attachments/bo-cards/all', {
      params: overviewParams(filters),
    });
    return response.data;
  },

  uploadBOCard: async ({ groupId, beneficiaryId, volunteerId, period, file }: BOCardUploadInput): Promise<BOCardAttachment> => {
    const response = await apiClient.post<BOCardAttachment>('v1/attachments/bo-cards', file, {
      params: {
        group_id: groupId,
        beneficiary_id: beneficiaryId,
        volunteer_id: volunteerId,
        period,
        filename: file.name,
      },
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
      },
    });
    return response.data;
  },

  update: async (id: number, data: AttachmentUpdateInput): Promise<BOCardAttachment> => {
    const response = await apiClient.patch<BOCardAttachment>(`v1/attachments/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`v1/attachments/${id}`);
  },

  downloadBOCardsArchive: async (filters: BOCardOverviewFilters): Promise<void> => {
    const response = await apiClient.get<Blob>('v1/attachments/bo-cards/all/download', {
      params: overviewParams(filters, false),
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: 'application/zip' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filenameFromDisposition(response.headers['content-disposition']);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
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
