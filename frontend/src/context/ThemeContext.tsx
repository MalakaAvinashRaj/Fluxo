import { createContext, useContext } from 'react'
import type { ReactNode } from 'react'

interface ThemeCtx { theme: 'dark' }

const ThemeContext = createContext<ThemeCtx>({ theme: 'dark' })

export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <ThemeContext.Provider value={{ theme: 'dark' }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
