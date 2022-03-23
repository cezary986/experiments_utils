import { ExperimentRun } from './experiment-run.model';

export interface Experiment {
  url: string;
  id: number;
  name: string;
  description: string;
  last_run: ExperimentRun | null;
  is_running: boolean;
  has_errors: boolean;
}
