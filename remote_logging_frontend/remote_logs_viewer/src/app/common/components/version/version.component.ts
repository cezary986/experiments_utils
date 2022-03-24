import { Component } from '@angular/core';
import { ModalController } from '@ionic/angular';
import packageJson from '../../../../../package.json';
import { VersionService } from './service/version.service';

@Component({
  selector: 'app-version',
  templateUrl: './version.component.html',
  styleUrls: ['./version.component.scss'],
})
export class VersionComponent {
  public appVersion: string = packageJson.version;
  public serverVersion: string = packageJson.version;

  constructor(
    private modalController: ModalController,
    private versionService: VersionService
  ) {
    this.versionService.getVersion().subscribe((res) => {
      this.serverVersion = res;
    });
  }

  public dismissModal() {
    this.modalController.dismiss();
  }
}
