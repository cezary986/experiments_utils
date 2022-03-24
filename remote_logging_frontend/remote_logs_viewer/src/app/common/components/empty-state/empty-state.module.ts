import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EmptyStateComponent } from './empty-state.component';
import { TranslateModule } from '@ngx-translate/core';
import { IonicModule } from '@ionic/angular';

@NgModule({
  declarations: [EmptyStateComponent],
  imports: [CommonModule, TranslateModule, IonicModule],
  exports: [EmptyStateComponent],
})
export class EmptyStateModule {}
