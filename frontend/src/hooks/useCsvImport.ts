import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importService } from '@/services/importService';
import type { ImportEntity } from '@/types';

/** CSV import mutation; refreshes the entity list once anything got imported. */
export function useCsvImport(entity: ImportEntity) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => importService.importCsv(entity, file),
    onSuccess: (report) => {
      if (report.imported > 0) {
        queryClient.invalidateQueries({ queryKey: [entity] });
      }
    },
  });
}
