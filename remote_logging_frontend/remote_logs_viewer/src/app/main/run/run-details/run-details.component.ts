import { Component, Input, OnInit } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import {
  ConfigExecution,
  ExperimentRun,
} from 'src/app/common/models/experiment-run.model';
import { ExperimentsRunsService } from 'src/app/common/services/experiments-runs.service';
import { RefreshService } from 'src/app/common/services/refresh.service';

@Component({
  selector: 'app-run-details',
  templateUrl: './run-details.component.html',
  styleUrls: ['./run-details.component.scss'],
})
export class RunDetailsComponent {
  public data: ExperimentRun;
  @Input() set run(value: ExperimentRun) {
    this.data = value;

    if (value.configs_execution) {
      this.configsFailed = [];
      this.configsFinished = [];
      this.configsRunning = [];
      Object.values(value.configs_execution).forEach(
        (configInfo: ConfigExecution) => {
          this.steps = configInfo.steps;
          if (configInfo.finished) {
            configInfo.finished = new Date(configInfo.finished);

            let took: any =
              configInfo.finished.getTime() -
              new Date(this.data.started).getTime();
            took = new Date(took);
            configInfo.took = {
              days: took.getDate() - 1,
              hours: took.getHours() - 1,
              minutes: took.getMinutes(),
              seconds: took.getSeconds(),
            };
            if (configInfo.has_errors) {
              this.configsFailed.push(configInfo);
            } else {
              this.configsFinished.push(configInfo);
            }
          } else {
            this.configsRunning.push(configInfo);
          }
        }
      );
    }
  }
  private _active: boolean;
  @Input() set active(active: boolean) {
    this._active = active;
  }
  private ngUnsubscribe: Subject<void> = new Subject();
  public configsFailed: ConfigExecution[];
  public configsFinished: ConfigExecution[];
  public configsRunning: ConfigExecution[];
  public steps: string[];

  constructor(
    private translate: TranslateService,
    private runService: ExperimentsRunsService,
    private refreshService: RefreshService
  ) {
    this.refreshService
      .listenToRefresh()
      .pipe(takeUntil(this.ngUnsubscribe))
      .subscribe((event) => {
        this.refresh(event);
      });
  }

  public refresh(event?) {
    this.runService.getRun(this.data.id).subscribe(
      (res) => {
        this.run = res;
        event?.complete();
      },
      (completed) => {
        event?.completed();
      }
    );
  }
}
