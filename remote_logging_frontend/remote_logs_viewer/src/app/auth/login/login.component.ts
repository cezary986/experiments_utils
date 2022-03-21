import { Component, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { NavController } from '@ionic/angular';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent implements OnDestroy {
  public form: FormGroup;
  public loading: boolean = false;
  public invalidCredentials: boolean = false;
  private onEnterListener: (event: any) => void;

  constructor(
    private authService: AuthService,
    private formBuilder: FormBuilder,
    private navController: NavController,
  ) {
    this.form = this.formBuilder.group({
      login: [null, [Validators.required]],
      password: [null, [Validators.required]],
    });
    this.authService.checkLoginStatus().subscribe((isLoggedIn: boolean) => {
      if (isLoggedIn) {
        this.onLoginSuccess();
      }
    });
    this.onEnterListener = (event) => {
      // Number 13 is the "Enter" key on the keyboard
      if (event.keyCode === 13 && this.form.valid) {
        // Cancel the default action, if needed
        event.preventDefault();
        this.onLoginClick();
      }
    };
    document.addEventListener('keyup', this.onEnterListener);
  }

  public onLoginClick() {
    this.loading = true;

    this.authService
      .login(this.form.value.login, this.form.value.password)
      .subscribe(
        (res) => {
          this.onLoginSuccess();
        },
        (error) => {
          this.loading = false;
          if (error.status !== undefined && error.status === 401) {
            this.invalidCredentials = true;
          } else {
            throw error;
          }
        },
        () => {
          this.loading = false;
        }
      );
  }

  public onLoginSuccess() {
    this.navController.navigateBack(['']);
  }

  ngOnDestroy(): void {
    document.removeEventListener('keyup', this.onEnterListener);
  }
}
