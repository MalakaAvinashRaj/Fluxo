import { useState, useCallback } from 'react'
import { ApiError } from '../services/api'
import { Logger } from '../utils/logger'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
}

interface UseApiReturn<T, Args extends unknown[]> extends UseApiState<T> {
  execute: (...args: Args) => Promise<T | null>
  reset: () => void
}

export function useApi<T, Args extends unknown[]>(
  apiFunction: (...args: Args) => Promise<T>,
  immediate = false
): UseApiReturn<T, Args> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: immediate,
    error: null,
  })

  const logger = new Logger('useApi')

  const execute = useCallback(async (...args: Args): Promise<T | null> => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }))
      
      const result = await apiFunction(...args)
      
      setState({
        data: result,
        loading: false,
        error: null,
      })
      
      return result
    } catch (error) {
      const apiError = error as ApiError
      logger.error('API call failed:', apiError)
      
      setState({
        data: null,
        loading: false,
        error: apiError,
      })
      
      return null
    }
  }, [apiFunction, logger])

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    })
  }, [])

  return {
    ...state,
    execute,
    reset,
  }
}