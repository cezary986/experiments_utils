import { TestBed } from '@angular/core/testing';

import { ExperimentsRunsService } from './experiments-runs.service';

describe('ExperimentsRunsService', () => {
  let service: ExperimentsRunsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ExperimentsRunsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
