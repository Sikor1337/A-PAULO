import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axiosClient from '@/lib/api';

interface AuditEvent {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string;
  actor_display_name: string | null;
  context_type: string | null;
  context_id: string | null;
  changes: Record<string, unknown>;
  created_at: string;
}

interface HistoryButtonProps {
  path: string;
  entityName: string;
  compact?: boolean;
  className?: string;
}

const HistoryButton = ({ path, entityName, compact = false, className = '' }: HistoryButtonProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const { data: events, isLoading } = useQuery({
    queryKey: ['audit-history', path],
    queryFn: async () => {
      const response = await axiosClient.get<AuditEvent[]>(path);
      return response.data;
    },
    enabled: isOpen,
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pl-PL');
  };

  const formatAction = (action: string) => {
    const map: Record<string, string> = {
      CREATE: 'Utworzono',
      UPDATE: 'Zaktualizowano',
      DELETE: 'Usunięto',
    };
    return map[action] || action;
  };

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined || value === '') return '—';
    if (typeof value === 'boolean') return value ? 'tak' : 'nie';
    if (Array.isArray(value)) return value.length ? value.map(formatValue).join(', ') : '—';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className={className || 'rounded bg-blue-100 px-3 py-1.5 text-xs font-bold text-blue-700'}
        title={`Historia ${entityName}`}
      >
        Historia
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-lg bg-white p-6 dark:bg-slate-800">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Historia: {entityName}</h2>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-2xl font-bold text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              >
                ×
              </button>
            </div>

            {isLoading ? (
              <div className="text-center text-gray-600 dark:text-gray-400">Ładowanie...</div>
            ) : !events || events.length === 0 ? (
              <div className="text-center text-gray-600 dark:text-gray-400">Brak wpisów historii</div>
            ) : (
              <div className="space-y-4">
                {events.map((event) => (
                  <div key={`${event.id}-${event.created_at}`} className="border-l-4 border-blue-500 bg-gray-50 p-4 dark:bg-slate-700">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-semibold text-blue-700 dark:text-blue-400">{formatAction(event.action)}</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">{formatDate(event.created_at)}</span>
                    </div>
                    <div className="mb-2 text-sm text-gray-700 dark:text-gray-300">
                      Wykonane przez: <span className="font-medium">{event.actor_display_name || event.actor_id}</span>
                    </div>
                    {Object.keys(event.changes).length > 0 && (
                      <div className="mt-2 space-y-1 rounded bg-gray-100 p-2 text-sm dark:bg-slate-600">
                        {Object.entries(event.changes).map(([field, change]) => (
                          <div key={field} className="text-gray-700 dark:text-gray-300">
                            <span className="font-medium">{field}:</span>
                            {typeof change === 'object' && change !== null && 'old' in change && 'new' in change ? (
                              <span>
                                {' '}
                                <span className="text-red-600 dark:text-red-400">{formatValue(change.old)}</span> →{' '}
                                <span className="text-green-600 dark:text-green-400">{formatValue(change.new)}</span>
                              </span>
                            ) : (
                              <span className="text-gray-600 dark:text-gray-400"> {formatValue(change)}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default HistoryButton;
