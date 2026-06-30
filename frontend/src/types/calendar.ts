export type CalendarEventStatus = 'draft' | 'published' | 'cancelled';
export type CalendarEventVisibility = 'organization' | 'admins';

export interface CalendarEvent {
  id: number;
  uid: string;
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  timezone: string;
  is_all_day: boolean;
  location: string;
  recurrence_rule: string | null;
  status: CalendarEventStatus;
  visibility: CalendarEventVisibility;
  author_id: number;
  author_name: string;
  sequence: number;
  created_at: string;
  updated_at: string;
}

export interface CalendarEventInput {
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  timezone: string;
  is_all_day: boolean;
  location: string;
  recurrence_rule: string | null;
  status: CalendarEventStatus;
  visibility: CalendarEventVisibility;
}

export interface CalendarFilters {
  startsFrom?: string;
  startsTo?: string;
  status?: CalendarEventStatus | '';
  visibility?: CalendarEventVisibility | '';
  sort?: 'asc' | 'desc';
}

export interface FeedTokenStatus {
  has_active_token: boolean;
  created_at: string | null;
}

export interface FeedTokenCreated {
  feed_url: string;
  created_at: string;
  warning: string;
}
