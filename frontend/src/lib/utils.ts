import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseFlutterFiles(text: string) {
  const fileRegex = /-- FILE: (.*?)\n([\s\S]*?)(?=-- FILE:|$)/g
  const files = []
  let match

  while ((match = fileRegex.exec(text)) !== null) {
    files.push({
      path: match[1].trim(),
      content: match[2].trim(),
    })
  }

  return files
} 