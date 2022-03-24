import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VersionComponent } from './version.component';
import { TranslateModule } from '@ngx-translate/core';
import { IonicModule } from '@ionic/angular';

@NgModule({
  declarations: [VersionComponent],
  imports: [CommonModule, TranslateModule, IonicModule],
  exports: [VersionComponent],
})
export class VersionModule {}
