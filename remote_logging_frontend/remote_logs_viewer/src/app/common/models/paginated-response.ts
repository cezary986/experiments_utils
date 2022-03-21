export interface PaginatedResponse<T> {
  count: number;
  next: number;
  previous: number;
  results: T[];
}
