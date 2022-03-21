export interface Experiment {
  url: string;
  id: number;
  name: string;
  description: string;
  last_run: {
    id: number;
    started: string;
    finished: string;
    has_errors: boolean;
    finished_configs: number;
    number_of_configs: number;
  } | null;
  is_running: boolean;
  has_errors: boolean;
}
