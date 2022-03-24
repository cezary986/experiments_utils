import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RunsRoutingModule } from './runs-routing.module';
import { RunsComponent } from './runs.component';
import { IonicModule } from '@ionic/angular';
import { StatusDotModule } from 'src/app/common/components/status-dot/status-dot.module';
import { TranslateModule } from '@ngx-translate/core';
import { EmptyStateModule } from 'src/app/common/components/empty-state/empty-state.module';

@NgModule({
  declarations: [RunsComponent],
  imports: [
    CommonModule,
    TranslateModule,
    StatusDotModule,
    IonicModule,
    EmptyStateModule,
    RunsRoutingModule,
  ],
})
export class RunsModule {}
