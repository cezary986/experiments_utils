export interface LogEntry {
  id: number;
  timestamp_string: Date;
  timestamp: Date;
  logger: string;
  config_name?: any;
  filename: string;
  function_name: string;
  line_number: number;
  level: string;
  stack_info?: any;
  message: string;
}
