import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpHeaders,
} from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor() {}
  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    const headers: HttpHeaders = new HttpHeaders({
      Authorization: `Token ${localStorage.getItem(AuthService.TOKEN_KEY)}`
    });
    request = request.clone({ withCredentials: true, headers: headers });
    return next.handle(request);
  }
}
