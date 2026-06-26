import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { attachmentService } from '@/services/attachmentService';
import { parseApiError } from '@/lib/errors';
import type { AttachmentUpdateInput, BOCardAttachment, BOCardUploadInput } from '@/types';

export function useBOCardAttachments(groupId: number | null, enabled = true) {
  return useQuery<BOCardAttachment[]>({
    queryKey: ['bo-card-attachments', groupId],
    queryFn: () => attachmentService.listBOCards(groupId as number),
    enabled: enabled && groupId !== null,
  });
}

export function useBOCardAttachmentActions(groupId: number | null) {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['bo-card-attachments', groupId] });

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
