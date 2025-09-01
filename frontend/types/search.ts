export interface Player {
  id: string
  name: string
  team?: string
}

export interface PlayData {
  GAME_ID: string
  EVENTNUM: number
  PERIOD: number
  PCTIMESTRING: string
  HOMEDESCRIPTION?: string
  VISITORDESCRIPTION?: string
  SCORE?: string
  SCOREMARGIN?: string
}

export interface VideoLinks {
  nba_stats?: string
  nba_video?: string
  nba_game?: string
  youtube_search?: string
}

export interface SearchResult {
  id: string
  playData: PlayData
  previewThumbnail: string
  watchLinks: VideoLinks
  description: string
  metadata: {
    date: Date
    gameId: string
    teams: [string, string]
    quarter: number
    timeRemaining: string
    players: Player[]
    action: string
  }
}

export interface SearchThread {
  id: string
  query: string
  timestamp: Date
  aiResponse: {
    summary: string
    resultCount: number
    insights: string[]
  }
  results: SearchResult[]
  status: 'loading' | 'complete' | 'error' | 'loading-more'
  hasMore?: boolean
  offset?: number
  limit?: number
}

export interface SearchFilters {
  sport?: string
  limit?: number
  offset?: number
  season?: string
  team?: string
  player?: string
}

export interface SearchRequest {
  query: string
  filters?: SearchFilters | Record<string, any>
  limit?: number
  offset?: number
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  entities: {
    player?: string
    player_id?: string
    action?: string
    season?: string
    team?: string
    time_range?: string
    sport?: string
  }
  aiResponse: {
    summary: string
    resultCount: number
    insights: string[]
  }
  hasMore?: boolean
  offset?: number
  limit?: number
}