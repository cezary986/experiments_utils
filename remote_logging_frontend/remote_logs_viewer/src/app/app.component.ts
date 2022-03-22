import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { NavController, ToastController } from '@ionic/angular';
import { Select } from '@ngxs/store';
import { Observable } from 'rxjs';
import { AuthService } from './auth/services/auth.service';
import { User } from './common/models/user.model';
import { AppBarAction, AppBarService } from './common/services/app-bar.service';
import { NavigationService } from './common/services/navigation.service';
import { RefreshService } from './common/services/refresh.service';
import { CurrentUserState } from './store/current_user/store';
import { initializeApp, deleteApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import { environment } from 'src/environments/environment';
import { AppError } from './common/errors/app-error';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent implements OnInit {
  @Select(CurrentUserState) currentUser: Observable<User>;
  public appBarActions: Observable<AppBarAction[]>;
  private firebaseApp: any;

  title = 'af-notification';
  message: any = null;
  public notificationsAllowed: boolean = false;

  public requestPermission() {
    Notification.requestPermission().then((getperm) => {
      if (getperm !== 'denied') {
        this.notificationsAllowed = true;
        const messaging = getMessaging();
        getToken(messaging, { vapidKey: environment.firebaseConfig.vapidKey })
          .then((currentToken) => {
            if (currentToken) {
              console.log('Hurraaa!!! we got the token.....');
              console.log(currentToken);
            } else {
              this.notificationsAllowed = false;
              throw new AppError(this.translate.instant('errors.notifications_error'));
            }
          })
          .catch((err) => {
            this.notificationsAllowed = false;
            throw new AppError(this.translate.instant('errors.notifications_error'));
          });
      }
    });
  }
  listen() {
    const messaging = getMessaging();
    onMessage(messaging, (payload) => {
      console.log('Message received. ', payload);
      this.message = payload;
    });
  }

  constructor(
    private translate: TranslateService,
    private navController: NavController,
    private appBarService: AppBarService,
    private authService: AuthService,
    public navigationService: NavigationService,
    private refreshService: RefreshService
  ) {
    this.appBarActions = this.appBarService.getActions();
    this.authService.authorized.subscribe((authorized: boolean) => {
      if (authorized) {
        this.firebaseApp = initializeApp(environment.firebaseConfig);
      } else {
        deleteApp(this.firebaseApp);
      }
    });
  }

  ngOnInit(): void {
    this.requestPermission();
    this.listen();
  }

  public doRefresh(event) {
    this.refreshService.emitRefresh(event.target);
  }

  public onLogoutClick() {
    this.authService.logout();
  }

  public goBack() {
    this.navController.back();
  }
}
