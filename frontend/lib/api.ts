import { SearchRequest, SearchResponse } from '@/types/search'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class SearchAPI {
  static async search(query: string, limit: number = 15, offset: number = 0): Promise<SearchResponse> {
    try {
      // Create an AbortController for timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 120000) // 120 second timeout (2 minutes)

      // Use real search endpoint
      const response = await fetch(`${API_BASE_URL}/api/v1/search/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          filters: {},
          limit,
          offset
        } as SearchRequest),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('Search timeout')
        throw new Error('Search took too long. Please try a simpler query.')
      }
      console.error('Search error:', error)
      throw error
    }
  }

  // Direct PlayDex search for raw video data
  static async searchDirect(query: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/search/search/direct`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query })
      })

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('PlayDex direct search error:', error)
      throw error
    }
  }
}