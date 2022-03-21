import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatusDotComponent } from './status-dot.component';
import { IonicModule } from '@ionic/angular';

@NgModule({
  declarations: [StatusDotComponent],
  imports: [CommonModule, IonicModule],
  exports: [StatusDotComponent],
})
export class StatusDotModule {}
