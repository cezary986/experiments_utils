import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})
export class NavigationService {
  public isNested = false;

  constructor(private router: Router) {
    this.router.events.subscribe(() => {
      this.isNested = window.location.pathname.split('/').length - 1 > 1;
    });
  }
}
