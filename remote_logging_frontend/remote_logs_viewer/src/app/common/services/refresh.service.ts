import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class RefreshService {
  public enableRefresh: boolean;
  private refeshEvent: Subject<{ complete: () => void }>;

  constructor() {
    this.enableRefresh = true;
    this.refeshEvent = new Subject();
  }

  public emitRefresh(event: any) {
    this.refeshEvent.next(event);
  }

  public listenToRefresh(): Observable<{ complete: () => void }> {
    return this.refeshEvent;
  }
}
