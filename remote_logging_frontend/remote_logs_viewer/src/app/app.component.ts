import { Location } from '@angular/common';
import { Component } from '@angular/core';
import { NavController } from '@ionic/angular';
import { Select } from '@ngxs/store';
import { Observable } from 'rxjs';
import { AuthService } from './auth/services/auth.service';
import { User } from './common/models/user.model';
import { AppBarAction, AppBarService } from './common/services/app-bar.service';
import { NavigationService } from './common/services/navigation.service';
import { RefreshService } from './common/services/refresh.service';
import { CurrentUserState } from './store/current_user/store';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent {
  @Select(CurrentUserState) currentUser: Observable<User>;
  public appBarActions: Observable<AppBarAction[]>;

  constructor(
    private location: Location,
    private navController: NavController,
    private appBarService: AppBarService,
    private authService: AuthService,
    public navigationService: NavigationService,
    private refreshService: RefreshService
  ) {
    this.appBarActions = this.appBarService.getActions();
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
