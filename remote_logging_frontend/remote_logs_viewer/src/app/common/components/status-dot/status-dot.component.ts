import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-status-dot',
  templateUrl: './status-dot.component.html',
  styleUrls: ['./status-dot.component.scss'],
})
export class StatusDotComponent {
  @Input() killed: boolean;
  @Input() failed: boolean;
  @Input() finished: boolean;
  @Input() neverRunned: boolean;
}
