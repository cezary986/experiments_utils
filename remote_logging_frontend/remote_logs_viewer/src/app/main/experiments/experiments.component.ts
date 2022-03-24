import { Component, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { Experiment } from 'src/app/common/models/experiment.model';
import { ExperimentsService } from 'src/app/common/services/experiments.service';
import {
  AlertController,
  NavController,
  ToastController,
} from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-experiments',
  templateUrl: './experiments.component.html',
  styleUrls: ['./experiments.component.scss'],
})
export class ExperimentsComponent implements OnDestroy {
  public items: Experiment[];
  private ngUnsubscribe: Subject<void> = new Subject();

  constructor(
    private translate: TranslateService,
    public toastController: ToastController,
    private navController: NavController,
    public alertController: AlertController,
    private experimentsService: ExperimentsService
  ) {
    this.fetchItems();
  }

  private fetchItems(event?) {
    this.experimentsService.getExperiments().subscribe(
      (res) => {
        this.items = res;
        event?.target?.complete();
      },
      (error) => {
        event?.target?.complete();
      }
    );
  }

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
    this.ngUnsubscribe.complete();
  }

  public onExperimentClick(experiment: Experiment) {
    this.navController.navigateForward(['experiments', experiment.id, 'runs']);
  }

  public onRemoveClick(experiment: Experiment) {
    this.alertController
      .create({
        header: this.translate.instant('experiments.remove_confirm.title'),
        message: this.translate.instant('experiments.remove_confirm.content', {
          experimentName: experiment.name,
        }),
        buttons: [
          {
            text: this.translate.instant('no'),
            role: 'cancel',
            cssClass: 'secondary',
            id: 'cancel-button',
          },
          {
            text: this.translate.instant('yes'),
            id: 'confirm-button',
            handler: () => {
              this.experimentsService
                .removeExperiment(experiment.id)
                .subscribe((res) => {
                  this.toastController
                    .create({
                      message: this.translate.instant('experiments.removed', {
                        experimentName: experiment.name,
                      }),
                      duration: 2000,
                    })
                    .then((toast) => {
                      toast.present();
                    });
                  this.refresh();
                });
            },
          },
        ],
      })
      .then((alert: HTMLIonAlertElement) => {
        alert.present();
      });
  }

  public refresh(event?) {
    this.items = null;
    this.fetchItems(event);
  }
}
