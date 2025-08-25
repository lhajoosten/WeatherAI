// Logging utilities for client-side logging

export interface LogLevel {
  value: number;
  label: string;
}

export const LOG_LEVELS = {
  DEBUG: { value: 0, label: 'DEBUG' },
  INFO: { value: 1, label: 'INFO' },
  WARN: { value: 2, label: 'WARN' },
  ERROR: { value: 3, label: 'ERROR' },
} as const;

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: Date;
  data?: unknown;
  source?: string;
}

class Logger {
  private level: LogLevel = LOG_LEVELS.INFO;
  private isDevelopment = import.meta.env.DEV;

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  private shouldLog(level: LogLevel): boolean {
    return level.value >= this.level.value;
  }

  private formatMessage(level: LogLevel, message: string, data?: unknown): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] ${level.label}:`;
    
    if (data !== undefined) {
      return `${prefix} ${message} ${JSON.stringify(data)}`;
    }
    
    return `${prefix} ${message}`;
  }

  debug(message: string, data?: unknown): void {
    if (this.shouldLog(LOG_LEVELS.DEBUG) && this.isDevelopment) {
      console.debug(this.formatMessage(LOG_LEVELS.DEBUG, message, data));
    }
  }

  info(message: string, data?: unknown): void {
    if (this.shouldLog(LOG_LEVELS.INFO)) {
      console.info(this.formatMessage(LOG_LEVELS.INFO, message, data));
    }
  }

  warn(message: string, data?: unknown): void {
    if (this.shouldLog(LOG_LEVELS.WARN)) {
      console.warn(this.formatMessage(LOG_LEVELS.WARN, message, data));
    }
  }

  error(message: string, data?: unknown): void {
    if (this.shouldLog(LOG_LEVELS.ERROR)) {
      console.error(this.formatMessage(LOG_LEVELS.ERROR, message, data));
    }
  }

  // For structured logging with client log collection
  log(level: LogLevel, message: string, data?: unknown, source?: string): LogEntry {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date(),
      data,
      source,
    };

    if (this.shouldLog(level)) {
      const method = level.value >= LOG_LEVELS.ERROR.value ? 'error' :
                    level.value >= LOG_LEVELS.WARN.value ? 'warn' :
                    level.value >= LOG_LEVELS.INFO.value ? 'info' : 'debug';
      
      console[method](this.formatMessage(level, message, data));
    }

    return entry;
  }
}

// Singleton logger instance
export const logger = new Logger();

// Set development level if in dev mode
if (import.meta.env.DEV) {
  logger.setLevel(LOG_LEVELS.DEBUG);
}