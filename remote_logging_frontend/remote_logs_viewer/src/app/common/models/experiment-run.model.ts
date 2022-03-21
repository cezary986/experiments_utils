import { Experiment } from './experiment.model';

export interface ExperimentRun {
  id: number;
  experiment: Experiment;
  started: Date;
  finished?: Date;
  has_errors: boolean;
  finished_configs: number;
  number_of_configs: number;
  configs_execution?: { [config_name: string]: ConfigExecution };
}

export interface ConfigExecution {
  config_name: string;
  steps: string[];
  current_step?: number;
  finished?: Date;
  has_errors?: boolean;
  steps_completed?: { [step_name: string]: Date };
  took?: {
    days: number,
    hours: number,
    minutes: number,
    seconds: number,
  };
}
