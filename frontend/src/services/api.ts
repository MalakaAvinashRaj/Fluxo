import { ENV } from '../config/environment'
import { Logger } from '../utils/logger'

export class ApiError extends Error {
  status?: number
  code?: string
  details?: unknown

  constructor(message: string, code?: string, status?: number, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

export interface ApiResponse<T = unknown> {
  data: T
  success: boolean
  message?: string
  timestamp: string
}

export type SessionData = {
  session_id: string
  user_id: string
  created_at: string
  is_active: boolean
  message_count: number
}

export interface ChatRequest {
  message: string
  autonomous?: boolean
  stream?: boolean
}

export interface ChatResponse {
  response: string
  tool_calls?: number
  session_id: string
  timestamp: string
}

class ApiService {
  private baseURL: string
  private timeout: number
  private retryAttempts: number
  private retryDelay: number
  private logger: Logger

  constructor() {
    this.baseURL = ENV.API_BASE_URL
    this.timeout = ENV.API_TIMEOUT
    this.retryAttempts = ENV.RETRY_ATTEMPTS
    this.retryDelay = ENV.RETRY_DELAY
    this.logger = new Logger('ApiService')
  }

  private async fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })
      
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      throw error
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    attempts: number = this.retryAttempts
  ): Promise<T> {
    try {
      return await requestFn()
    } catch (error) {
      if (attempts > 1 && this.isRetryableError(error)) {
        this.logger.warn(`Request failed, retrying... (${this.retryAttempts - attempts + 1}/${this.retryAttempts})`)
        await this.sleep(this.retryDelay)
        return this.retryRequest(requestFn, attempts - 1)
      }
      throw error
    }
  }

  private isRetryableError(error: unknown): boolean {
    if (error instanceof ApiError && error.status === 429) return false
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) return true
    if (error instanceof Error && error.name === 'AbortError') return true
    return false
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private handleApiError(error: unknown, context: string): ApiError {
    this.logger.error(`API Error in ${context}:`, error)

    // Pass ApiErrors through as-is (e.g. rate limit errors)
    if (error instanceof ApiError) return error

    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      return new ApiError(
        `Unable to connect to backend service. Please ensure the server is running at ${this.baseURL}`,
        'CONNECTION_REFUSED'
      )
    }
    
    if (error instanceof Error && error.name === 'AbortError') {
      return new ApiError(
        'Request timed out. Please try again.',
        'TIMEOUT'
      )
    }

    if (error instanceof Error) {
      return new ApiError(
        error.message,
        'UNKNOWN_ERROR',
        undefined,
        error
      )
    }

    return new ApiError(
      'An unexpected error occurred',
      'UNKNOWN_ERROR',
      undefined,
      error
    )
  }

  async healthCheck(): Promise<{ status: 'healthy' | 'unhealthy'; timestamp: string }> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseURL}/health`)
      
      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`)
      }
      
      return {
        status: 'healthy',
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      this.logger.error('Health check failed:', error)
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString()
      }
    }
  }

  async createSession(userId: string): Promise<SessionData> {
    return this.retryRequest(async () => {
      try {
        const response = await this.fetchWithTimeout(`${this.baseURL}/sessions`, {
          method: 'POST',
          body: JSON.stringify({ user_id: userId }),
        })

        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After') ?? '60'
          throw new ApiError(
            `Too many sessions created. Please wait ${Math.ceil(Number(retryAfter) / 60)} minute(s) before trying again.`,
            'RATE_LIMITED',
            429
          )
        }

        if (!response.ok) {
          throw new Error(`Failed to create session: ${response.status} ${response.statusText}`)
        }

        const data = await response.json()
        this.logger.info('Session created successfully:', data.session_id)
        return data
      } catch (error) {
        throw this.handleApiError(error, 'createSession')
      }
    })
  }

  async getSession(sessionId: string): Promise<SessionData> {
    return this.retryRequest(async () => {
      try {
        const response = await this.fetchWithTimeout(`${this.baseURL}/sessions/${sessionId}`)

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Session not found or expired')
          }
          throw new Error(`Failed to get session: ${response.status} ${response.statusText}`)
        }

        const data = await response.json()
        return data
      } catch (error) {
        throw this.handleApiError(error, 'getSession')
      }
    })
  }

  async sendMessage(sessionId: string, request: ChatRequest): Promise<ChatResponse> {
    return this.retryRequest(async () => {
      try {
        const response = await this.fetchWithTimeout(`${this.baseURL}/sessions/${sessionId}/chat`, {
          method: 'POST',
          body: JSON.stringify(request),
        })

        if (!response.ok) {
          throw new Error(`Failed to send message: ${response.status} ${response.statusText}`)
        }

        const data = await response.json()
        this.logger.info('Message sent successfully')
        return data
      } catch (error) {
        throw this.handleApiError(error, 'sendMessage')
      }
    })
  }

  async sendMessageStream(sessionId: string, message: string, onChunk: (chunk: any) => void): Promise<void> {
    return this.retryRequest(async () => {
      try {
        this.logger.info('Sending streaming message to session:', sessionId)
        
        const response = await this.fetchWithTimeout(`${this.baseURL}/sessions/${sessionId}/chat/stream`, {
          method: 'POST',
          body: JSON.stringify({
            message,
            stream: true,
            autonomous: true,
            max_iterations: 10
          }),
        })

        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After') ?? '60'
          throw new ApiError(
            `Rate limit reached. Please wait ${Math.ceil(Number(retryAfter) / 60)} minute(s) before sending more messages.`,
            'RATE_LIMITED',
            429
          )
        }

        if (!response.ok) {
          throw new Error(`Failed to send message: ${response.status} ${response.statusText}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('No response body reader available')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
              const data = line.trim().substring(6)
              if (data === '[DONE]') {
                return
              }
              
              try {
                const chunk = JSON.parse(data)
                onChunk(chunk)
              } catch (e) {
                this.logger.warn('Failed to parse chunk:', data)
              }
            }
          }
        }
      } catch (error) {
        throw this.handleApiError(error, 'sendMessageStream')
      }
    })
  }

  async warmupSession(
    sessionId: string,
    onPhase: (event: { phase: string; message: string; previewUrl?: string }) => void
  ): Promise<void> {
    try {
      this.logger.info('Starting container warmup for session:', sessionId)

      // No timeout here — warmup can take up to 3 minutes
      const response = await fetch(`${this.baseURL}/sessions/${sessionId}/warmup`, {
        headers: { Accept: 'text/event-stream' },
      })

      if (!response.ok) {
        throw new Error(`Warmup failed: ${response.status} ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body reader available')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            const data = line.trim().substring(6)
            if (data === '[DONE]') return
            try {
              const event = JSON.parse(data)
              onPhase(event)
            } catch {
              // ignore malformed chunks
            }
          }
        }
      }
    } catch (error) {
      throw this.handleApiError(error, 'warmupSession')
    }
  }
}

export const apiService = new ApiService()