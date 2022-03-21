import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { User } from '../models/user.model';

@Injectable({
  providedIn: 'root',
})
export class CurrentUserService {
  constructor(private http: HttpClient) {}

  public getCurrentUser(): Observable<User> {
    return this.http.get<User>(`${environment.baseApiUrl}/user`);
  }
}
