import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class VersionService {
  constructor(private http: HttpClient) {}

  public getVersion(): Observable<string> {
    return this.http
      .get<{ version: string }>(`${environment.baseApiUrl}/version`)
      .pipe(map((res) => res.version));
  }
}
