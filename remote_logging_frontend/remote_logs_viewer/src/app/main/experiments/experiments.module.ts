import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ExperimentsRoutingModule } from './experiments-routing.module';
import { ExperimentsComponent } from './experiments.component';
import { IonicModule } from '@ionic/angular';
import { StatusDotModule } from 'src/app/common/components/status-dot/status-dot.module';
import { TranslateModule } from '@ngx-translate/core';

@NgModule({
  declarations: [ExperimentsComponent],
  imports: [
    CommonModule,
    TranslateModule,
    IonicModule,
    StatusDotModule,
    ExperimentsRoutingModule,
  ],
})
export class ExperimentsModule {}
