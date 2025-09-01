'use client'

import { Play, ExternalLink } from 'lucide-react'
import { SearchResult } from '@/types/search'
import { cn } from '@/lib/utils'

interface LinkCardProps {
  result: SearchResult
  className?: string
}

export function LinkCard({ result, className }: LinkCardProps) {
  return (
    <div className={cn(
      "glass-panel overflow-hidden group",
      "hover:transform hover:scale-[1.02] transition-all duration-300",
      "hover:shadow-2xl hover:shadow-blue-500/10",
      className
    )}>
      {/* Thumbnail with overlay */}
      <a 
        href={result.watchLinks.nba_video || result.watchLinks.nba_stats}
        target="_blank"
        rel="noopener noreferrer"
        className="block relative aspect-video overflow-hidden"
      >
        <img 
          src={result.previewThumbnail} 
          alt={result.description}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        
        {/* Play button */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 transform scale-75 group-hover:scale-100">
            <div className="bg-blue-500/90 backdrop-blur-sm rounded-full p-4 shadow-2xl">
              <Play className="w-8 h-8 text-white fill-white" />
            </div>
          </div>
        </div>
        
        {/* Live indicator (if applicable) */}
        {result.metadata.quarter === 4 && (
          <div className="absolute top-3 right-3 bg-red-500 text-white text-xs px-2 py-1 rounded-full font-bold">
            CLUTCH
          </div>
        )}
      </a>
      
      {/* Content */}
      <div className="p-4">
        {/* Description */}
        <p className="text-sm font-semibold text-white line-clamp-2 mb-3">
          {result.description}
        </p>
        
        {/* Metadata */}
        <div className="text-xs text-gray-400 mb-4 space-y-1">
          <div className="font-medium text-gray-300">{result.metadata.teams.join(' vs ')}</div>
          <div>Q{result.metadata.quarter} • {result.metadata.timeRemaining}</div>
        </div>
        
        {/* Action buttons */}
        <div className="flex gap-2">
          <a 
            href={result.watchLinks.nba_video || result.watchLinks.nba_stats}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 inline-flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-lg
              bg-blue-500/20 text-blue-400 border border-blue-500/30
              hover:bg-blue-500/30 hover:text-white hover:border-blue-400/50
              transition-all duration-200 font-medium"
          >
            {result.watchLinks.nba_video ? 'Watch' : 'View'}
            <ExternalLink className="w-3 h-3" />
          </a>
          <a 
            href={result.watchLinks.youtube_search}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg
              bg-white/5 text-gray-400 border border-white/10
              hover:bg-white/10 hover:text-white hover:border-white/20
              transition-all duration-200"
          >
            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
          </a>
        </div>
      </div>
    </div>
  )
}