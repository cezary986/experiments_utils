import { Experiment } from './experiment.model';

export interface ExperimentRun {
  id: number;
  experiment: Experiment;
  started: Date;
  finished?: Date;
  has_errors: boolean;
  killed: boolean;
  finished_configs: number;
  number_of_configs: number;
  configs_execution?: { [config_name: string]: ConfigExecution };
}

export interface ConfigExecution {
  config_name: string;
  steps: string[];
  current_step?: number;
  finished?: Date;
  finishedTimestamp?: number;
  has_errors?: boolean;
  steps_completed?: { [step_name: string]: Date };
  error_message?: string;
  stack_trace?: string;
  took?: {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
  };
}
