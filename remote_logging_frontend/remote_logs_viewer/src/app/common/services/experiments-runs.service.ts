import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { ExperimentRun } from '../models/experiment-run.model';

@Injectable({
  providedIn: 'root',
})
export class ExperimentsRunsService {
  constructor(private http: HttpClient) {}

  public getRun(runId: number): Observable<ExperimentRun> {
    return this.http.get<ExperimentRun>(
      `${environment.baseApiUrl}/experiments_runs/${runId}`
    );
  }

  public getRuns(experimentName: string): Observable<ExperimentRun[]> {
    return this.http.get<ExperimentRun[]>(
      `${environment.baseApiUrl}/experiments_runs/?experiment_name=${encodeURI(
        experimentName
      )}`
    );
  }

  public removeRun(id: number): Observable<void> {
    return this.http.delete<void>(
      `${environment.baseApiUrl}/experiments_runs/${id}`
    );
  }
}
