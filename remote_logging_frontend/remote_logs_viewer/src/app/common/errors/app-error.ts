export class AppError {
  constructor(
    public originalError?: any,
    public customMessage?: string,
    public customTitle?: string
  ) {}
}
