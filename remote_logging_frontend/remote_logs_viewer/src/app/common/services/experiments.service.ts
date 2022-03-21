import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { Experiment } from '../models/experiment.model';

@Injectable({
  providedIn: 'root',
})
export class ExperimentsService {
  constructor(private http: HttpClient) {}

  public getExperiments(): Observable<Experiment[]> {
    return this.http.get<Experiment[]>(`${environment.baseApiUrl}/experiments`);
  }

  public getExperiment(id: number): Observable<Experiment> {
    return this.http.get<Experiment>(
      `${environment.baseApiUrl}/experiments/${id}`
    );
  }

  public removeExperiment(id: number): Observable<void> {
    return this.http.delete<void>(
      `${environment.baseApiUrl}/experiments/${id}`
    );
  }
}
