import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RunDetailsComponent } from './run-details.component';
import { TranslateModule } from '@ngx-translate/core';
import { IonicModule } from '@ionic/angular';
import { StatusDotModule } from 'src/app/common/components/status-dot/status-dot.module';

@NgModule({
  declarations: [RunDetailsComponent],
  imports: [CommonModule, TranslateModule, StatusDotModule, IonicModule],
  exports: [RunDetailsComponent],
})
export class RunDetailsModule {}
