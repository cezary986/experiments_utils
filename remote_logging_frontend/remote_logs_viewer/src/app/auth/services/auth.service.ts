import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from 'src/environments/environment';
import { map, mergeMap } from 'rxjs/operators';
import { CurrentUserService } from 'src/app/common/services/current-user.service';
import { Store } from '@ngxs/store';
import { SetCurrentUser } from 'src/app/store/current_user/store';
import { NavController } from '@ionic/angular';
import * as localforage from 'localforage';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  public static readonly TOKEN_KEY = 'token';

  private loggedIn: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(
    true
  );

  constructor(
    private navController: NavController,
    private store: Store,
    private http: HttpClient,
    private currentUserService: CurrentUserService
  ) {
    this.fetchCurrentUser();
  }

  private fetchCurrentUser() {
    this.currentUserService.getCurrentUser().subscribe((res) => {
      this.store.dispatch(new SetCurrentUser(res));
    });
  }

  public get isLoggedIn(): boolean {
    return this.loggedIn.value;
  }

  public get authorized(): Observable<boolean> {
    return this.loggedIn;
  }

  public login(
    username: string,
    password: string
  ): Observable<{ token: string }> {
    return this.http
      .post<{ token: string }>(
        `${environment.baseApiUrl}/auth/login`,
        {
          username: username,
          password: password,
        },
        {
          withCredentials: true,
        }
      )
      .pipe(
        mergeMap((res) => {
          const result = new Subject<any>();
          localforage.setItem(
            AuthService.TOKEN_KEY,
            res.token,
            function (error) {
              if (error) {
                result.error(error);
              } else {
                this.fetchCurrentUser();
                this.loggedIn.next(true);
                result.next(res);
              }
              result.complete();
            }
          );
          return result;
        })
      );
  }

  public checkLoginStatus(): Observable<boolean> {
    const result = new Subject<boolean>();
    localforage.getItem('key', function (error, token) {
      if (error) {
        result.error(error);
      } else {
        result.next(token !== null && token !== undefined);
      }
      result.complete();
    });
    return result;
  }

  public logout(): Observable<any> {
    const result = this.http.post(`${environment.baseApiUrl}/auth/logout`, {});
    result.subscribe((res) => {
      this.store.dispatch(new SetCurrentUser(null));
      this.loggedIn.next(false);

      this.navController.navigateBack(['/auth', 'login']);
    });
    return result;
  }
}
