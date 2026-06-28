import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { attachmentService } from '@/services/attachmentService';
import { parseApiError } from '@/lib/errors';
import type {
  AttachmentUpdateInput,
  BOCardAttachment,
  BOCardOverviewFilters,
  BOCardOverviewResponse,
  BOCardUploadInput,
} from '@/types';

export function useBOCardAttachments(groupId: number | null, enabled = true) {
  return useQuery<BOCardAttachment[]>({
    queryKey: ['bo-card-attachments', groupId],
    queryFn: () => attachmentService.listBOCards(groupId as number),
    enabled: enabled && groupId !== null,
  });
}

export function useBOCardOverview(filters: BOCardOverviewFilters) {
  return useQuery<BOCardOverviewResponse>({
    queryKey: ['bo-card-overview', filters],
    queryFn: () => attachmentService.listBOCardsOverview(filters),
  });
}

export function useBOCardAttachmentActions(groupId: number | null) {
  const queryClient = useQueryClient();
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['bo-card-attachments', groupId] });
    queryClient.invalidateQueries({ queryKey: ['bo-card-overview'] });
  };

  const uploadBOCard = useMutation({
    mutationFn: (input: BOCardUploadInput) => attachmentService.uploadBOCard(input),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  const updateAttachment = useMutation({
    mutationFn: ({ id, data }: { id: number; data: AttachmentUpdateInput }) => attachmentService.update(id, data),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  const deleteAttachment = useMutation({
    mutationFn: (id: number) => attachmentService.delete(id),
    onSuccess: invalidate,
    onError: () => alert('Nie udało się usunąć pliku.'),
  });

  return { uploadBOCard, updateAttachment, deleteAttachment };
}

export function useBOCardOverviewActions(filters: BOCardOverviewFilters) {
  const queryClient = useQueryClient();
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['bo-card-overview'] });
    queryClient.invalidateQueries({ queryKey: ['bo-card-attachments'] });
  };

  const updateAttachment = useMutation({
    mutationFn: ({ id, data }: { id: number; data: AttachmentUpdateInput }) => attachmentService.update(id, data),
    onSuccess: invalidate,
    onError: (error) => alert(parseApiError(error)),
  });

  const deleteAttachment = useMutation({
    mutationFn: (id: number) => attachmentService.delete(id),
    onSuccess: invalidate,
    onError: () => alert('Nie udało się usunąć pliku.'),
  });

  const downloadArchive = useMutation({
    mutationFn: () => attachmentService.downloadBOCardsArchive(filters),
    onError: () => alert('Nie udało się pobrać załączników.'),
  });

  return { updateAttachment, deleteAttachment, downloadArchive };
}
