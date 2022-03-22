import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import { map } from 'rxjs/operators';
import { CurrentUserService } from 'src/app/common/services/current-user.service';
import { Store } from '@ngxs/store';
import { SetCurrentUser } from 'src/app/store/current_user/store';
import { NavController } from '@ionic/angular';

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
    this.checkLoginStatus().subscribe(
      (res) => {
        this.fetchCurrentUser();
      },
      (error) => {
        this.logout();
      }
    );
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
        map((res) => {
          localStorage.setItem(AuthService.TOKEN_KEY, res.token);
          this.fetchCurrentUser();
          this.loggedIn.next(true);
          return res;
        })
      );
  }

  public checkLoginStatus(): Observable<boolean> {
    const status = this.http.get<{ logged_in: boolean }>(
      `${environment.baseApiUrl}/auth/check_login`,
      { withCredentials: true }
    );
    return status.pipe(
      map((res) => {
        this.loggedIn.next(res.logged_in);
        return res.logged_in;
      })
    );
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
