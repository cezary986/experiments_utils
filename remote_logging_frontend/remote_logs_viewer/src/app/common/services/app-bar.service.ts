import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

interface AppBarActionItem {
  id?: string;
  icon: string;
  name: string;
  handler: () => void;
}

export interface AppBarAction {
  icon: string;
  name: string;
  handler: () => void;
}

export interface AppBarActionAssigner {
  ngUnsubscribe: Subject<void>;
}

@Injectable({
  providedIn: 'root',
})
export class AppBarService {
  private actions: BehaviorSubject<AppBarAction[]> = new BehaviorSubject([]);

  public getActions(): Observable<AppBarAction[]> {
    return this.actions;
  }

  public addAction(self: AppBarActionAssigner, action: AppBarAction) {
    (action as AppBarActionItem).id = `${self.constructor.name}_${action.name}`;
    const newValue = this.actions.value;
    newValue.push(action);
    this.actions.next(newValue);
    self.ngUnsubscribe.subscribe(() => {
      const newValue = this.actions.value.filter(
        (a: AppBarActionItem) => a.id !== (action as AppBarActionItem).id
      );
      this.actions.next(newValue);
    });
  }

  public removeAction(self: OnDestroy, name: string) {
    const newValue = this.actions.value.filter(
      (action: AppBarActionItem) =>
        action.id !== `${self.constructor.name}_${action.name}`
    );
    this.actions.next(newValue);
  }
}
