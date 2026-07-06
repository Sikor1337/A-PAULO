export interface AuditChange {
  old: unknown;
  new: unknown;
}

export interface AuditEvent {
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
