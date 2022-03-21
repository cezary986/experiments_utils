import { ChangeDetectorRef, Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { IonSegment, IonSlide, IonSlides } from '@ionic/angular';
import { ExperimentRun } from 'src/app/common/models/experiment-run.model';
import { ExperimentsRunsService } from 'src/app/common/services/experiments-runs.service';

@Component({
  selector: 'app-run',
  templateUrl: './run.component.html',
  styleUrls: ['./run.component.scss'],
})
export class RunComponent implements OnInit {
  @ViewChild(IonSlides) slides: IonSlides;
  @ViewChild(IonSegment) tabs: IonSegment;
  public currentTab = 0;
  public runId: number;
  public experimentRun: ExperimentRun;
  slideOpts = {
    initialSlide: this.currentTab,
    speed: 400,
  };
  constructor(
    private activatedRoute: ActivatedRoute,
    private changeDetector: ChangeDetectorRef,
    private experimentRunService: ExperimentsRunsService
  ) {}

  ngOnInit(): void {
    this.runId = this.activatedRoute.snapshot.paramMap['params'].runId;
    this.experimentRunService
      .getRun(this.runId)
      .subscribe((res: ExperimentRun) => {
        this.experimentRun = res;
      });
  }

  public onTabSwiped(event) {
    event.getActiveIndex().then((a) => {
      this.currentTab = a;
      this.changeDetector.detectChanges();
    });
  }

  public onTabClicked(event) {
    this.currentTab = event.detail.value;
    this.changeDetector.detectChanges();
    this.slides.slideTo(this.currentTab);
  }
}
