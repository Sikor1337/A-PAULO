/** Standard DRF paginated list response (PageNumberPagination). */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Entity that has a numeric primary key. */
export interface WithId {
  id: number;
}
