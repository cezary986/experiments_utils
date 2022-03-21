import { Subject } from 'rxjs';

export class Screen {
  public ngUnsubscribe: Subject<void> = new Subject();

  ngOnDestroy(): void {
    this.ngUnsubscribe.next();
    this.ngUnsubscribe.complete();
  }
}
