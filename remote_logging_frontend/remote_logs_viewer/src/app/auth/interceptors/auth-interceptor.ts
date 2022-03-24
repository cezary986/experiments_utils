import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpHeaders,
} from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import * as localforage from 'localforage';
import { AuthService } from '../services/auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private getToken(): Observable<string> {
    const result = new Subject<string>();
    localforage.getItem(AuthService.TOKEN_KEY, (error, token: string) => {
      if (error) {
        result.error(error);
      } else {
        result.next(token);
      }
      result.complete();
    });
    return result;
  }

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    return this.getToken().pipe(
      mergeMap((token: string) => {
        const headers: HttpHeaders = new HttpHeaders({
          Authorization: `Token ${token}`,
        });
        request = request.clone({ withCredentials: true, headers: headers });
        return next.handle(request);
      })
    );
  }
}
