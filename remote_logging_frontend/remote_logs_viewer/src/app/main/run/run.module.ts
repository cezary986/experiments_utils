import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RunRoutingModule } from './run-routing.module';
import { RunComponent } from './run.component';
import { TranslateModule } from '@ngx-translate/core';
import { IonicModule } from '@ionic/angular';
import { FormsModule } from '@angular/forms';
import { LogsModule } from './logs/logs.module';
import { RunDetailsModule } from './run-details/run-details.module';

@NgModule({
  declarations: [RunComponent],
  imports: [
    CommonModule,
    FormsModule,
    TranslateModule,
    LogsModule,
    RunDetailsModule,
    IonicModule,
    RunRoutingModule,
  ],
})
export class RunModule {}
