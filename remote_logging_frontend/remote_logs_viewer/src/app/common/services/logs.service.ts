import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { LogEntry } from '../models/log-entry.model';
import { PaginatedResponse } from '../models/paginated-response';

@Injectable({
  providedIn: 'root',
})
export class LogsService {
  static readonly DEFAULT_LIMIT = 25;

  constructor(private http: HttpClient) {}

  public getLogs(
    runId: number,
    offset: number,
    level?: string,
    limit?: number
  ): Observable<PaginatedResponse<LogEntry>> {
    let params = `?limit=${
      limit ? limit : LogsService.DEFAULT_LIMIT
    }&offset=${offset}`;
    if (level) {
      params = `${params}&level=${level}`;
    }
    return this.http.get<PaginatedResponse<LogEntry>>(
      `${environment.baseApiUrl}/logs/${runId}${params}`
    );
  }
}
