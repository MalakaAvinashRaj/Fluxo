import { ENV, isProduction } from '../config/environment'

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export class Logger {
  private context: string
  private level: LogLevel

  constructor(context: string) {
    this.context = context
    this.level = ENV.LOG_LEVEL as LogLevel
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: Record<LogLevel, number> = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3,
    }

    return levels[level] >= levels[this.level]
  }

  private formatMessage(level: LogLevel, message: string, ...args: unknown[]): void {
    if (!this.shouldLog(level)) return

    const timestamp = new Date().toISOString()
    const prefix = `[${timestamp}] [${level.toUpperCase()}] [${this.context}]`

    if (isProduction) {
      // In production, use structured logging
      const logData = {
        timestamp,
        level,
        context: this.context,
        message,
        data: args.length > 0 ? args : undefined,
      }

      switch (level) {
        case 'debug':
        case 'info':
          console.log(JSON.stringify(logData))
          break
        case 'warn':
          console.warn(JSON.stringify(logData))
          break
        case 'error':
          console.error(JSON.stringify(logData))
          break
      }
    } else {
      // In development, use readable logging
      switch (level) {
        case 'debug':
          console.debug(`${prefix} ${message}`, ...args)
          break
        case 'info':
          console.info(`${prefix} ${message}`, ...args)
          break
        case 'warn':
          console.warn(`${prefix} ${message}`, ...args)
          break
        case 'error':
          console.error(`${prefix} ${message}`, ...args)
          break
      }
    }
  }

  debug(message: string, ...args: unknown[]): void {
    this.formatMessage('debug', message, ...args)
  }

  info(message: string, ...args: unknown[]): void {
    this.formatMessage('info', message, ...args)
  }

  warn(message: string, ...args: unknown[]): void {
    this.formatMessage('warn', message, ...args)
  }

  error(message: string, ...args: unknown[]): void {
    this.formatMessage('error', message, ...args)
  }
}