import { ErrorHandler, Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { ToastController } from '@ionic/angular';
import { AppError } from './app-error';
import { AuthService } from 'src/app/auth/services/auth.service';
import { TranslateService } from '@ngx-translate/core';

@Injectable({
  providedIn: 'root',
})
export class CommonErrorHandler implements ErrorHandler {
  private TOAST_DURATION = 2000;

  constructor(
    private translate: TranslateService,
    private authService: AuthService,
    public toastController: ToastController
  ) {}

  private handleHttpError(error: HttpErrorResponse | AppError) {
    const httpError: HttpErrorResponse =
      error instanceof AppError ? error.originalError : error;
    const errorTitle = (error as any).customTitle
      ? (error as any).customTitle
      : (httpError as any).error?.name;
    const errorMessage = (error as any).message
      ? (error as any).message
      : this.translate.instant('errors.server_error');
    switch (httpError.status) {
      case 0:
        // Błąd połączenia z serwerem
        setTimeout(() => {
          this.toastController
            .create({
              message: errorTitle
                ? errorTitle
                : this.translate.instant('errors.no_connection'),
              duration: this.TOAST_DURATION,
            })
            .then((toast) => {
              toast.present();
            });
        }, 100);
        break;
      case 400:
        this.authService.logout();
        break;
      case 401:
        this.authService.logout();
        break;
      case 403:
        this.authService.logout();
        break;
      case 404:
        this.toastController
          .create({
            message: errorMessage,
            duration: 2000,
          })
          .then((toast) => {
            toast.present();
          });
        break;
      case 409:
        this.toastController
          .create({
            message: errorMessage,
            duration: this.TOAST_DURATION,
          })
          .then((toast) => {
            toast.present();
          });

        break;
      default:
        this.toastController
          .create({
            message: errorMessage,
            duration: this.TOAST_DURATION,
          })
          .then((toast) => {
            toast.present();
          });
        break;
    }
  }

  private handleCustomError(error: AppError) {
    const errorTitle = error.customTitle
      ? (error as any).customTitle
      : this.translate.instant('errors.app_error');
    const errorMessage = error.customMessage;

    this.toastController
      .create({
        message: errorMessage,
        duration: this.TOAST_DURATION,
      })
      .then((toast) => {
        toast.present();
      });
  }

  handleError(error): void {
    console.error(error)
    if (
      (error instanceof AppError &&
        error.originalError instanceof HttpErrorResponse) ||
      error.status !== undefined
    ) {
      this.handleHttpError(error);
    } else if (error instanceof AppError) {
      this.handleCustomError(error);
    } else {
      this.toastController
        .create({
          message: this.translate.instant('errors.app_error'),
          duration: this.TOAST_DURATION,
        })
        .then((toast) => {
          toast.present();
        });
    }
  }
}
