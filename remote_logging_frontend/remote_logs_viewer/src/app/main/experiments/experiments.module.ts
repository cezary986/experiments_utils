import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ExperimentsRoutingModule } from './experiments-routing.module';
import { ExperimentsComponent } from './experiments.component';
import { IonicModule } from '@ionic/angular';
import { StatusDotModule } from 'src/app/common/components/status-dot/status-dot.module';
import { TranslateModule } from '@ngx-translate/core';
import { EmptyStateModule } from 'src/app/common/components/empty-state/empty-state.module';

@NgModule({
  declarations: [ExperimentsComponent],
  imports: [
    CommonModule,
    TranslateModule,
    IonicModule,
    StatusDotModule,
    EmptyStateModule,
    ExperimentsRoutingModule,
  ],
})
export class ExperimentsModule {}
