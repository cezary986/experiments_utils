import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import {
  AlertController,
  NavController,
  ToastController,
} from '@ionic/angular';
import { TranslateService } from '@ngx-translate/core';
import { Subject } from 'rxjs';
import { ExperimentRun } from 'src/app/common/models/experiment-run.model';
import { Experiment } from 'src/app/common/models/experiment.model';
import { ExperimentsRunsService } from 'src/app/common/services/experiments-runs.service';
import { ExperimentsService } from 'src/app/common/services/experiments.service';

@Component({
  selector: 'app-runs',
  templateUrl: './runs.component.html',
  styleUrls: ['./runs.component.scss'],
})
export class RunsComponent implements OnDestroy, OnInit {
  private experimentId: number;
  public experiment: Experiment;
  public items: ExperimentRun[];
  private ngUnsubscribe: Subject<void> = new Subject();

  constructor(
    private translate: TranslateService,
    public toastController: ToastController,
    private navController: NavController,
    public alertController: AlertController,
    private activatedRoute: ActivatedRoute,
    private experimentService: ExperimentsService,
    private runsService: ExperimentsRunsService
  ) {}

  ngOnInit(): void {
    this.experimentId = this.activatedRoute.snapshot.paramMap['params'].id;
    this.experimentService
      .getExperiment(this.experimentId)
      .subscribe((res: Experiment) => {
        this.experiment = res;
        this.fetchItems();
      });
  }

  private fetchItems(event?) {
    this.runsService.getRuns(this.experiment.name).subscribe(
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

  public onRunClick(run: ExperimentRun) {
    this.navController.navigateForward([
      'experiments',
      this.experiment.id,
      'runs',
      run.id,
    ]);
  }

  public onRemoveClick(run: ExperimentRun) {
    this.alertController
      .create({
        header: this.translate.instant('runs.remove_confirm.title'),
        message: this.translate.instant('runs.remove_confirm.content'),
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
              this.runsService.removeRun(run.id).subscribe((res) => {
                this.toastController
                  .create({
                    message: this.translate.instant('runs.removed'),
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
