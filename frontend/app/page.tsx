'use client'

import { useState } from 'react'
import { SearchBar } from '@/components/search/SearchBar'
import { LinkCard } from '@/components/search/LinkCard'
import { LegalNotice } from '@/components/ui/LegalNotice'
import { SearchThread, SearchResult } from '@/types/search'
import { SearchAPI } from '@/lib/api'

// Function suggestions - NBA specific queries
const FUNCTION_SUGGESTIONS = [
  "Giannis poster dunks from 2024",
  "Curry logo threes",
  "Game winners in the playoffs",
  "LeBron chase down blocks",
  "Jokic no-look passes"
]

export default function Home() {
  const [threads, setThreads] = useState<SearchThread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)

  const handleSearch = async (query: string, isLoadMore: boolean = false) => {
    setIsSearching(true)
    
    let targetThread: SearchThread
    
    if (isLoadMore && activeThreadId) {
      // Loading more results for existing thread
      const existingThread = threads.find(t => t.id === activeThreadId)
      if (!existingThread) return
      
      targetThread = existingThread
      setThreads(prev => prev.map(thread => 
        thread.id === activeThreadId 
          ? { ...thread, status: 'loading-more' }
          : thread
      ))
    } else {
      // Create new thread
      targetThread = {
        id: Date.now().toString(),
        query,
        timestamp: new Date(),
        aiResponse: {
          summary: "Searching for clips...",
          resultCount: 0,
          insights: []
        },
        results: [],
        status: 'loading',
        offset: 0,
        limit: 15
      }
      
      setThreads(prev => [...prev, targetThread])
      setActiveThreadId(targetThread.id)
    }
    
    try {
      // Calculate offset for pagination
      const offset = isLoadMore ? (targetThread.results?.length || 0) : 0
      
      // Call backend API
      const response = await SearchAPI.search(query || targetThread.query, 15, offset)
      
      // Update thread with results
      setThreads(prev => prev.map(thread => 
        thread.id === targetThread.id 
          ? {
              ...thread,
              status: 'complete',
              results: isLoadMore 
                ? [...(thread.results || []), ...response.results]
                : response.results,
              aiResponse: isLoadMore && thread.aiResponse.summary !== "Searching for clips..."
                ? thread.aiResponse  // Keep existing AI response when loading more
                : response.aiResponse,
              hasMore: response.hasMore,
              offset: response.offset,
              limit: response.limit
            }
          : thread
      ))
    } catch (error: any) {
      console.error('Search failed:', error)
      
      // Update thread with error
      const errorMessage = error.message || 'An error occurred'
      const isTimeout = errorMessage.includes('took too long')
      
      setThreads(prev => prev.map(thread => 
        thread.id === targetThread.id 
          ? {
              ...thread,
              status: 'error',
              aiResponse: {
                summary: isTimeout 
                  ? `The search took too long. Try a simpler query like "LeBron dunks" or "Curry threes"`
                  : `Sorry, I couldn't search for "${query}". ${errorMessage}`,
                resultCount: 0,
                insights: isTimeout
                  ? ['NBA API can be slow sometimes', 'Try searching without specific dates or seasons', 'Simple queries work best']
                  : ['Make sure the backend server is running on port 8000', 'Check your internet connection']
              }
            }
          : thread
      ))
    } finally {
      setIsSearching(false)
    }
  }

  const activeThread = threads.find(t => t.id === activeThreadId)
  const hasSearched = threads.length > 0

  return (
    <div className="min-h-screen bg-black">
      <div className="flex flex-col h-screen">
        {!hasSearched ? (
          // Landing page - Claude style
          <div className="flex-1 flex flex-col items-center justify-center px-4">
            <div className="w-full max-w-3xl mx-auto">
              {/* Title */}
              <div className="text-center" style={{ marginBottom: '80px' }}>
                <h1 className="text-[48px] leading-[1.1] font-bold text-white tracking-tight whitespace-nowrap">
                  What NBA moment can I find for you?
                </h1>
              </div>
              
              {/* Main search area */}
              <div>
                {/* Search box */}
                <div style={{ marginBottom: '60px' }}>
                  <SearchBar 
                    onSearch={handleSearch} 
                    isLoading={isSearching}
                    placeholder="LeBron dunks from the 2023 playoffs"
                  />
                </div>
                
                {/* Function suggestions */}
                <div className="flex flex-wrap gap-4 justify-center" style={{ marginTop: '20px' }}>
                  {FUNCTION_SUGGESTIONS.map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => handleSearch(suggestion)}
                      style={{ 
                        padding: '16px 32px',
                        fontSize: '17px',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '16px',
                        background: 'transparent',
                        color: 'rgba(255, 255, 255, 0.8)',
                        transition: 'all 0.2s'
                      }}
                      className="hover:bg-white/[0.02] hover:border-white/25 hover:text-white"
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.25)';
                        e.currentTarget.style.color = 'white';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                        e.currentTarget.style.color = 'rgba(255, 255, 255, 0.8)';
                      }}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Legal notice at bottom */}
            <div className="absolute bottom-6 left-0 right-0 px-4">
              <div className="max-w-3xl mx-auto">
                <LegalNotice className="text-gray-600 text-xs text-center" />
              </div>
            </div>
          </div>
        ) : (
          // Search results interface
          <div className="flex-1 flex flex-col bg-black">
            {/* Simple header */}
            <header className="border-b border-white/10 px-4 py-4">
              <div className="max-w-6xl mx-auto flex items-center justify-between">
                <h1 className="text-xl font-semibold text-white">PlayDex</h1>
                <button 
                  onClick={() => {
                    setThreads([])
                    setActiveThreadId(null)
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-300 
                    hover:text-white transition-colors"
                >
                  New Search
                </button>
              </div>
            </header>

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-4xl mx-auto px-4 py-8">
                {activeThread && (
                  <div className="space-y-8">
                    {/* User query */}
                    <div className="flex justify-end">
                      <div className="max-w-[80%] bg-white/[0.06] border border-white/10 
                        rounded-2xl rounded-br-sm px-5 py-3">
                        <p className="text-white">{activeThread.query}</p>
                      </div>
                    </div>
                    
                    {/* AI Response and Results */}
                    <div className="space-y-6">
                      <div className="bg-white/[0.02] border border-white/10 rounded-xl p-6">
                        <p className="text-white leading-relaxed">{activeThread.aiResponse.summary}</p>
                        {activeThread.aiResponse.insights.length > 0 && (
                          <ul className="mt-4 space-y-2">
                            {activeThread.aiResponse.insights.map((insight, i) => (
                              <li key={i} className="text-gray-400 flex items-start">
                                <span className="mr-2 text-gray-500">•</span>
                                <span>{insight}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      
                      {/* Results grid */}
                      {(activeThread.status === 'complete' || activeThread.status === 'loading-more') && activeThread.results.length > 0 && (
                        <>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {activeThread.results.map(result => (
                              <LinkCard key={result.id} result={result} />
                            ))}
                          </div>
                          
                          {/* Load more button */}
                          {activeThread.hasMore && (
                            <div className="flex justify-center mt-8">
                              <button
                                onClick={() => handleSearch(activeThread.query, true)}
                                disabled={activeThread.status === 'loading-more' || isSearching}
                                className="px-6 py-3 bg-white/[0.03] border border-white/10 
                                  rounded-md text-white font-medium
                                  hover:bg-white/[0.06] hover:border-white/20
                                  disabled:opacity-50 disabled:cursor-not-allowed
                                  transition-all duration-200"
                              >
                                {activeThread.status === 'loading-more' ? 'Loading more...' : 'Load More'}
                              </button>
                            </div>
                          )}
                        </>
                      )}
                      
                      {/* Loading state */}
                      {activeThread.status === 'loading' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {[1, 2, 3].map(i => (
                            <div key={i} className="bg-white/[0.02] border border-white/10 
                              rounded-xl h-64 animate-pulse" />
                          ))}
                        </div>
                      )}
                      
                      {/* Error state */}
                      {activeThread.status === 'error' && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
                          <p className="text-red-400">
                            There was an error with your search. Please try again.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Bottom search bar */}
            <div className="border-t border-white/10 px-4 py-4">
              <div className="max-w-3xl mx-auto">
                <SearchBar 
                  onSearch={handleSearch} 
                  isLoading={isSearching}
                />
              </div>
            </div>
            
            {/* Legal notice */}
            <div className="px-4 py-3 border-t border-white/5">
              <div className="max-w-4xl mx-auto">
                <LegalNotice className="text-gray-600 text-xs text-center" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}