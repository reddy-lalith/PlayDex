'use client'

import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchBarProps {
  onSearch: (query: string) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
}

export function SearchBar({ 
  onSearch, 
  isLoading = false, 
  placeholder = "Message PlayDex...",
  className 
}: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSearch(query.trim())
      setQuery('')
    }
  }

  return (
    <div className={cn(
      "relative w-full max-w-3xl mx-auto",
      className
    )}>
      <div className={cn(
        "relative flex items-center",
        "bg-transparent rounded-2xl border border-white/20",
        "min-h-[64px]",
        isFocused && "border-white/40 bg-white/[0.02]"
      )}>
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              handleSubmit()
            }
          }}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={isLoading}
          style={{ paddingLeft: '24px', paddingRight: '80px' }}
          className={cn(
            "w-full bg-transparent",
            "text-white placeholder:text-white/40",
            "focus:outline-none",
            "h-[64px]",
            "text-[17px] font-normal"
          )}
        />
        
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || isLoading}
          className={cn(
            "absolute transition-all",
            "right-4 top-1/2 -translate-y-1/2 p-3 rounded-xl",
            "bg-black text-white hover:bg-gray-900",
            (!query.trim() || isLoading) && "opacity-30 cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}