import {
  AfterViewInit,
  Component,
  NgZone,
  OnInit,
  ViewChild,
} from '@angular/core';
import { IonContent, ModalController, NavController } from '@ionic/angular';
import { Select } from '@ngxs/store';
import { Observable } from 'rxjs';
import { AuthService } from './auth/services/auth.service';
import { User } from './common/models/user.model';
import { AppBarAction, AppBarService } from './common/services/app-bar.service';
import { NavigationService } from './common/services/navigation.service';
import { CurrentUserState } from './store/current_user/store';
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import { environment } from 'src/environments/environment';
import { AppError } from './common/errors/app-error';
import { TranslateService } from '@ngx-translate/core';
import { VersionComponent } from './common/components/version/version.component';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent implements OnInit, AfterViewInit {
  @Select(CurrentUserState) currentUser: Observable<User>;
  @ViewChild(IonContent) content: IonContent;
  public appBarActions: Observable<AppBarAction[]>;
  private firebaseApp: any;
  public darkThemeEnabled: boolean;

  public notificationsAllowed: boolean = false;

  constructor(
    private translate: TranslateService,
    private navController: NavController,
    private appBarService: AppBarService,
    private authService: AuthService,
    public navigationService: NavigationService,
    public modalController: ModalController
  ) {
    this.appBarActions = this.appBarService.getActions();
    this.authService.authorized.subscribe((authorized: boolean) => {
      if (authorized) {
        this.firebaseApp = initializeApp(environment.firebaseConfig);
        this.navController.navigateForward('/experiments');
      }
    });
  }

  ngOnInit(): void {
    this.navController.navigateRoot(location.pathname);
    this.requestNotificationsPermission();
    this.listenToNotifications();
  }

  ngAfterViewInit(): void {
    if (
      (window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: dark)').matches) ||
      document.body.classList.contains('dark')
    ) {
      this.darkThemeEnabled = true;
    } else {
      this.darkThemeEnabled = false;
    }
  }

  public requestNotificationsPermission() {
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
              throw new AppError(
                this.translate.instant('errors.notifications_error')
              );
            }
          })
          .catch((err) => {
            this.notificationsAllowed = false;
            throw new AppError(
              this.translate.instant('errors.notifications_error')
            );
          });
      }
    });
  }

  private listenToNotifications() {
    const messaging = getMessaging();
    onMessage(messaging, (payload) => {
      console.log('Message received. ', payload);
    });
  }

  public onLogoutClick() {
    this.authService.logout();
  }

  public goBack() {
    this.navController.back();
  }

  async logScrollEnd($event) {
    console.log($event);

    if ($event.target.localName != 'ion-content') {
      // not sure if this is required, just playing it safe
      return;
    }

    const scrollElement = await $event.target.getScrollElement();
    console.log({ scrollElement });

    // minus clientHeight because trigger is scrollTop
    // otherwise you hit the bottom of the page before
    // the top screen can get to 80% total document height
    const scrollHeight =
      scrollElement.scrollHeight - scrollElement.clientHeight;
    console.log({ scrollHeight });

    const currentScrollDepth = $event.detail.scrollTop;
    console.log({ currentScrollDepth });

    const targetPercent = 80;

    let triggerDepth = (scrollHeight / 100) * targetPercent;
    console.log({ triggerDepth });

    if (currentScrollDepth > triggerDepth) {
      console.log(`Scrolled to ${targetPercent}%`);
      // this ensures that the event only triggers once

      // do your analytics tracking here
    }
  }

  public async onAboutAppClick() {
    const modal = await this.modalController.create({
      component: VersionComponent,
      cssClass: 'my-custom-class',
    });
    return await modal.present();
  }
}
