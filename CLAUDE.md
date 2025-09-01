# PlayDex - AI Sports Engine Development Guide

## Project Overview
**PlayDex** is an AI-powered sports search engine that allows users to search for specific sports clips using natural language queries. The interface is designed to mirror the clean, conversational experience of Claude and ChatGPT, making sports clip discovery as intuitive as having a conversation. **PlayDex does not host any video content** - it serves as an intelligent search and discovery layer that connects users to official video sources.

### Core Vision
- Natural language search with a Claude/ChatGPT-like interface
- Instant clip discovery with AI-generated summaries
- Links to official NBA video sources (no hosting)
- Conversational search experience with threaded history
- Clean, minimalistic glassmorphic design
- Scalable to support millions of users and all sports

### Design Philosophy
Just like Claude and ChatGPT revolutionized AI chat interfaces, PlayDex aims to revolutionize sports clip search by:
- **Centered Search Experience**: Main search bar in the center, just like Claude's message input
- **Conversation Threading**: Each search creates a conversation thread with AI responses
- **Progressive Disclosure**: Start simple, reveal complexity as needed
- **Intelligent Responses**: AI summarizes findings before showing clips
- **Legal Compliance**: All videos remain on official platforms

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend UI   │────▶│ EntityExtractor  │────▶│  SearchEngine   │
│  (React/Next)   │     │ (NLP Processing) │     │  (Query Logic)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
                        ┌─────────────────┐       ┌─────────────────┐
                        │   Sports APIs   │       │  Official NBA   │
                        │   (nba_api)     │       │  Video Sources  │
                        └─────────────────┘       └─────────────────┘
                                                  (YouTube, NBA.com)
                                                   
Note: PlayDex does NOT store or host any video content. All videos are 
served directly from official sources.
```

## Tech Stack

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **UI Library**: React with TypeScript
- **Styling**: Tailwind CSS with glassmorphism effects
- **State Management**: Zustand or Redux Toolkit
- **Search History**: IndexedDB for local storage
- **Video Player**: Video.js or custom player

### Backend
- **API Framework**: FastAPI (Python) or Node.js (Express/Fastify)
- **EntityExtractor**: 
  - spaCy or Hugging Face Transformers
  - Custom NER models for sports entities
  - Fuzzy matching for spell correction
- **SearchEngine**:
  - Python with nba_api library
  - Play-by-play data indexing
  - Redis for caching metadata (not videos)
- **Database**: PostgreSQL for metadata and search history
- **Queue System**: RabbitMQ or AWS SQS

### Infrastructure
- **Hosting**: AWS/GCP/Vercel
- **CDN**: For static assets only (no video hosting)
- **Caching**: Redis for API responses and metadata
- **Container**: Docker with Kubernetes
- **Monitoring**: DataDog or New Relic

### Legal Compliance
- **No Video Storage**: All videos remain on official platforms
- **Link Only**: PlayDex only provides links to official sources
- **Terms of Service**: Compliant with NBA and other leagues' ToS

## Core Components

### Current Engine Implementation (PlayDex Engine)

PlayDex now uses an advanced search engine with the following capabilities:

- **Advanced NLP**: Uses spaCy with custom matchers for player and team recognition
- **Fuzzy Matching**: RapidFuzz integration for handling misspellings and variations
- **Smart Query Understanding**: Extracts players, teams, actions, time ranges, and context
- **Direct Video Access**: Returns actual NBA video URLs and thumbnails
- **High Performance**: Optimized for speed with caching and efficient data processing

The engine is located in `/backend/app/services/playdex_engine/` and includes:
- `entity_extractor.py`: Advanced entity extraction with fuzzy matching
- `search_engine.py`: Core search logic with NBA API integration
- `keywords_constants.py`: Comprehensive keyword mappings
- `utils.py`: Helper functions for data processing

### 1. EntityExtractor Module

```python
class EntityExtractor:
    """
    Handles natural language processing for sports queries
    """
    
    def __init__(self):
        self.nlp_model = load_sports_ner_model()
        self.entity_db = EntityDatabase()
        
    def extract_entities(self, query: str) -> Dict:
        """
        Extract and normalize sports entities from user query
        
        Example:
        Input: "lebron james blocks in 2012"
        Output: {
            "player": "LeBron James",
            "player_id": "2544",
            "action": "blocks",
            "season": "2012-13",
            "sport": "basketball"
        }
        """
        
    def spell_check(self, text: str) -> str:
        """Correct common misspellings in sports queries"""
        
    def link_entities(self, entities: List) -> List:
        """Link entities to database IDs"""
```

### 2. SearchEngine Module

```python
class SearchEngine:
    """
    Queries sports APIs and returns filtered clips
    """
    
    def __init__(self):
        self.nba_client = NBAApiClient()
        self.cache = RedisCache()
        
    def search_clips(self, params: Dict) -> List[Clip]:
        """
        Search for clips based on extracted parameters
        """
        
    def filter_clips(self, clips: List, filters: Dict) -> List:
        """Apply additional filters like shot distance"""
        
    def enrich_metadata(self, clips: List) -> List:
        """Add detailed metadata to each clip"""
```

### 3. Video Retrieval Pipeline (Link-Only Approach)

**Important**: PlayDex does not store videos. We only fetch metadata and provide links to official sources.

#### Video Discovery Strategy:

```python
from nba_api.stats.endpoints import videoevents, playbyplayv2

class VideoLinkProvider:
    """
    Provides links to official NBA videos without storing content
    """
    
    def get_official_video_link(self, game_id: str, event_id: int) -> Dict:
        """
        Get official NBA video information without storing
        """
        
        # Step 1: Get video metadata from nba_api
        video_event = videoevents.VideoEvents(
            game_id=game_id, 
            game_event_id=event_id
        )
        video_data = video_event.get_dict()
        
        # Step 2: Extract thumbnails and metadata
        video_meta = video_data['resultSets']['Meta']['videoUrls'][0]
        uuid = video_meta['uuid']
        thumbnails = {
            'small': video_meta['stp'],   # Use for preview
            'medium': video_meta['mtp'],  
            'large': video_meta['ltp']    
        }
        
        # Step 3: Generate official NBA links (no direct video URLs)
        return {
            'uuid': uuid,
            'thumbnails': thumbnails,
            'official_links': {
                'nba_stats': f"https://www.nba.com/stats/events/?flag=1&GameID={game_id}&GameEventID={event_id}",
                'nba_game': f"https://www.nba.com/game/{game_id}",
                'youtube_search': self.generate_youtube_search_url(video_data)
            },
            'play_description': video_data['resultSets']['playlist'][0]['dsc']
        }
    
    def generate_youtube_search_url(self, play_data: Dict) -> str:
        """
        Generate YouTube search for official NBA channel
        """
        description = play_data['resultSets']['playlist'][0]['dsc']
        date = play_data['resultSets']['playlist'][0]['d']
        
        search_query = f"NBA {description} {date} official"
        return f"https://youtube.com/results?search_query={search_query}"
```

#### Safe Implementation Pattern:

```python
class SafeSearchEngine:
    """
    Search engine that respects copyright by linking only
    """
    
    def search_plays_with_links(self, query_params: Dict) -> List[Dict]:
        """
        Search for plays and provide links to official sources
        """
        results = []
        
        # 1. Get play-by-play data
        plays = self.get_plays_from_nba_api(query_params)
        
        # 2. For each play, get official links
        for play in plays:
            if play['EVENTNUM']:
                video_links = self.link_provider.get_official_video_link(
                    game_id=play['GAME_ID'],
                    event_id=play['EVENTNUM']
                )
                
                results.append({
                    'play_data': play,
                    'preview_thumbnail': video_links['thumbnails']['large'],
                    'watch_links': video_links['official_links'],
                    'description': video_links['play_description']
                })
                
        return results
```

#### Frontend Display (No Embedded Videos):

```typescript
interface PlayResult {
    playData: PlayByPlayData;
    previewThumbnail: string;
    watchLinks: {
        nba_stats: string;
        nba_game: string;
        youtube_search: string;
    };
    description: string;
}

const PlayCard: React.FC<{ result: PlayResult }> = ({ result }) => {
    return (
        <div className="glass-panel p-4">
            {/* Show thumbnail with play button overlay */}
            <div className="relative">
                <img 
                    src={result.previewThumbnail} 
                    alt={result.description}
                    className="w-full rounded-lg"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                    <PlayButton />
                </div>
            </div>
            
            {/* Play description */}
            <p className="mt-2 font-medium">{result.description}</p>
            
            {/* Links to official sources */}
            <div className="mt-3 flex gap-2">
                <a 
                    href={result.watchLinks.nba_stats}
                    target="_blank"
                    className="btn-primary"
                >
                    Watch on NBA.com
                </a>
                <a 
                    href={result.watchLinks.youtube_search}
                    target="_blank"
                    className="btn-secondary"
                >
                    Find on YouTube
                </a>
            </div>
        </div>
    );
};
```

#### Legal Compliance Notice:

```typescript
const LegalNotice = () => (
    <div className="text-sm text-gray-500 mt-4">
        PlayDex is a search engine that helps you discover official NBA content. 
        We do not host any videos. All video content is property of the NBA 
        and its partners. Click the links to watch on official platforms.
    </div>
);
```

## Frontend Structure

```
/src
├── app/
│   ├── layout.tsx          # Main layout with glassmorphic design
│   ├── page.tsx            # Home/Search page (Claude-like centered layout)
│   └── api/                # API routes
├── components/
│   ├── SearchBar/          # Central search (like Claude's message input)
│   ├── SearchHistory/      # Left sidebar (like Claude's chat history)
│   ├── ResultsContainer/   # Conversation-style results display
│   ├── ClipCard/           # Individual clip component
│   ├── ClipPlayer/         # Inline video player
│   ├── AIResponse/         # Formatted AI response component
│   └── ui/                 # Reusable UI components
├── hooks/
│   ├── useSearch.ts        # Search functionality
│   ├── useHistory.ts       # Search history management
│   └── useKeyboardShortcuts.ts  # Cmd/Ctrl+K for search focus
└── styles/
    └── globals.css         # Glassmorphism & Claude-inspired styles
```

### Claude/ChatGPT-Inspired Components

#### SearchBar Component
```typescript
interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

// Features:
// - Auto-resize like Claude's input
// - Keyboard shortcuts (Enter to search, Shift+Enter for new line)
// - Loading state with pulsing animation
// - Clear button on right when text present
// - Voice input option (future feature)
```

#### ConversationView Component
```typescript
interface ConversationViewProps {
  searches: SearchThread[];
  activeThreadId: string;
}

interface SearchThread {
  id: string;
  query: string;
  timestamp: Date;
  results: ClipResult[];
  aiSummary: string;
}

// Displays searches as conversation threads
// Smooth scrolling between searches
// Collapsible previous searches
```

## UI/UX Design Specifications

### Claude/ChatGPT-Inspired Interface

PlayDex's interface directly mirrors the clean, conversational design of Claude and ChatGPT:

#### **1. Landing Page (Empty State)**
- **Centered Search Bar**: Just like Claude/ChatGPT's message input, positioned in the middle of the screen
- **Logo & Tagline**: "PlayDex" logo above search bar with subtitle "AI Sports Engine"
- **Suggested Searches**: Below search bar, showing example queries like:
  - "Show me all LeBron James dunks from 2023 playoffs"
  - "Steph Curry 3-pointers from 40+ feet"
  - "Patrick Mahomes touchdown passes in 4th quarter"
- **Clean Background**: Subtle gradient with glassmorphic elements floating

#### **2. Main Interface Layout (After Search)**

```
┌─────────────────────────────────────────────────────────────┐
│  [PlayDex Logo]                              [New Search] [⚙️]│
├─────────────────┬───────────────────────────────────────────┤
│                 │                                             │
│  Search History │         Main Content Area                  │
│  (Left Sidebar) │                                             │
│                 │  ┌─────────────────────────────────────┐  │
│  Recent:        │  │                                       │  │
│  • LeBron      │  │    Search Bar (Always Visible)        │  │
│    blocks 2012 │  │    [🔍 Search for any sports moment] │  │
│  • Curry 3pts  │  │                                       │  │
│  • Mahomes TD  │  └─────────────────────────────────────┘  │
│                 │                                             │
│  Collections:   │         Search Results Grid                │
│  • Favorites   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  • Watch Later │  │ Clip │ │ Clip │ │ Clip │ │ Clip │     │
│                 │  └──────┘ └──────┘ └──────┘ └──────┘     │
└─────────────────┴───────────────────────────────────────────┘
```

#### **3. Key Design Elements Matching Claude/ChatGPT:**

**Search Bar Design**
- Large, rounded input field with subtle shadow
- Placeholder text: "Search any sports moment..."
- Send button on right (similar to Claude's send button)
- Auto-expanding for longer queries
- Shows loading animation during search (pulsing border)

**Conversation-Style Results**
- Results appear below search bar like chat messages
- Each search creates a "conversation thread"
- User query shown at top, followed by AI response with clips
- Smooth scroll animations as new results load

**Left Sidebar (Search History)**
- Collapsible like Claude's conversation list
- Shows truncated previous searches
- Hover reveals full query
- Click to reload previous search
- Delete option on hover

### Glassmorphism Design
```css
/* Glass effect matching modern Claude aesthetic */
.glass-panel {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}

/* Search bar with Claude-like styling */
.search-bar {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 16px 24px;
  font-size: 16px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  width: 100%;
  max-width: 680px; /* Same as Claude's input */
}

.search-bar:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Dark mode support */
.dark .glass-panel {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.dark .search-bar {
  background: rgba(40, 40, 40, 0.95);
  color: white;
}
```

### Interaction Patterns from Claude/ChatGPT:

#### **1. Search Flow**
- User types in center search bar
- Real-time suggestions appear below (like Claude's autocomplete)
- Press Enter or click Send button
- Search bar stays in place, results appear below
- Previous search moves up, creating a "conversation history"

#### **2. Results Presentation**
- **AI Response Format**: 
  ```
  User: "LeBron James blocks in 2012"
  
  PlayDex: Found 47 blocks by LeBron James from the 2011-12 season.
  Here are the most spectacular ones:
  
  [Grid of video clips with metadata]
  ```

#### **3. Clip Interaction (ChatGPT-like)**
- Click clip to expand inline (like ChatGPT's code blocks)
- Video player appears with controls
- Metadata shown below: date, teams, quarter, time
- Related clips suggested at bottom

#### **4. Progressive Disclosure**
- Start with top 8 results
- "Show more" button to load additional clips
- Infinite scroll with lazy loading
- Filters appear after initial search (don't clutter initial view)

### Search Interface (Claude-Style)
```typescript
interface SearchResult {
  id: string;
  videoUrl: string;
  thumbnailUrl: string;
  // AI-generated summary for each clip
  aiDescription: string;
  metadata: {
    date: Date;
    gameId: string;
    teams: [string, string];
    quarter: number;
    timeRemaining: string;
    players: Player[];
    action: string;
    shotDetails?: {
      distance: number;
      type: string;
      made: boolean;
    };
  };
}

interface SearchThread {
  id: string;
  query: string;
  timestamp: Date;
  aiResponse: {
    summary: string;
    resultCount: number;
    insights: string[];
  };
  results: SearchResult[];
  status: 'loading' | 'complete' | 'error';
}
```

### Mobile Responsive Design (Like Claude Mobile)
- Search bar remains centered and prominent
- Left sidebar becomes bottom sheet on mobile
- Touch-optimized clip cards
- Swipe gestures for navigation
- Full-screen video player on tap

## Database Schema

### Core Tables (No Video Storage)
```sql
-- Players table (multi-sport)
CREATE TABLE players (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    sport VARCHAR(50),
    team_id UUID,
    external_id VARCHAR(100), -- API-specific ID
    metadata JSONB
);

-- Play metadata table (no video storage)
CREATE TABLE plays (
    id UUID PRIMARY KEY,
    sport VARCHAR(50),
    game_id VARCHAR(100),
    event_id INTEGER,
    nba_uuid VARCHAR(100), -- NBA's video UUID for API calls
    play_description TEXT,
    game_date DATE,
    players JSONB,
    teams JSONB,
    play_type VARCHAR(50),
    metadata JSONB,
    search_vector tsvector, -- For full-text search
    created_at TIMESTAMPTZ
);

-- Search history
CREATE TABLE search_history (
    id UUID PRIMARY KEY,
    user_id UUID,
    query TEXT,
    entities JSONB,
    results_count INTEGER,
    created_at TIMESTAMPTZ
);

-- Cached NBA metadata (temporary cache only)
CREATE TABLE nba_metadata_cache (
    game_event_key VARCHAR(200) PRIMARY KEY, -- game_id + event_id
    nba_response JSONB, -- Cached API response
    thumbnail_urls JSONB, -- Quick access to thumbnails
    cached_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ -- Respect cache limits
);
```

## API Endpoints

### Main Search API
```typescript
// POST /api/v1/search/search
{
  "query": "LeBron James blocks in 2012",
  "filters": {
    "sport": "basketball",
    "limit": 20,
    "offset": 0
  }
}

// Response
{
  "results": [...],
  "total": 145,
  "entities": {
    "player": "LeBron James",
    "action": "blocks",
    "season": "2012-13"
  },
  "aiResponse": {
    "summary": "Found 145 clips matching 'LeBron James blocks in 2012'",
    "resultCount": 145,
    "insights": ["Showing clips featuring LeBron James", "Focused on blocks"]
  }
}
```

### Direct Search API (Raw Video Data)
```typescript
// POST /api/v1/search/search/direct
{
  "query": "lebron james points"
}

// Response (PlayDex Engine Format)
{
  "query": "lebron james points",
  "data": [{
    "Game_ID": "0022301195",
    "Game_Date": "2024-04-14T00:00:00",
    "Description": "James 2' Cutting Layup Shot (8 PTS) (Davis 2 AST)",
    "Video_Link": "https://videos.nba.com/nba/pbp/media/2024/04/14/0022301195/263/e50ffcb9-0d5d-4dbd-32e5-3b29209b672a_1280x720.mp4",
    "Thumbnail_Link": "https://videos.nba.com/nba/pbp/media/2024/04/14/0022301195/263/e50ffcb9-0d5d-4dbd-32e5-3b29209b672a_1280x720.jpg",
    // ... more fields
  }]
}
```

### Clip Details API
```typescript
// GET /api/clips/:id
{
  "id": "...",
  "videoUrl": "...",
  "metadata": {...},
  "relatedClips": [...]
}
```

## Scaling Considerations

### Performance Optimization (No Video Hosting Overhead)
1. **Lightweight Infrastructure**
   - No video storage costs
   - No bandwidth concerns for video streaming
   - Focus resources on search and discovery

2. **Caching Strategy**
   - Redis for play-by-play data
   - Thumbnail caching with CDN
   - Search results caching
   - No video URL caching (legal compliance)

3. **Database Optimization**
   - Index on player names and actions
   - Full-text search on play descriptions
   - Partitioning by season/date
   - No large video blob storage needed

### Multi-Sport Extension
```typescript
interface SportAdapter {
  extractEntities(query: string): SportEntities;
  searchAPI(params: any): Promise<Results>;
  generateOfficialLinks(data: any): LinkOptions;
  getThumbnails(data: any): ThumbnailUrls;
}

class BasketballAdapter implements SportAdapter {
  generateOfficialLinks(play: any): LinkOptions {
    return {
      official_site: `https://nba.com/game/${play.game_id}`,
      youtube: `https://youtube.com/c/NBA`,
      stats_page: `https://nba.com/stats/events/...`
    };
  }
}

class FootballAdapter implements SportAdapter {
  generateOfficialLinks(play: any): LinkOptions {
    return {
      official_site: `https://nfl.com/videos/...`,
      youtube: `https://youtube.com/c/NFL`,
      gamepass: `https://nfl.com/gamepass/...`
    };
  }
}
```

## Development Roadmap

### Phase 1: MVP (Basketball Only - Link-Based)
- [ ] Basic EntityExtractor with NBA players
- [ ] SearchEngine with nba_api integration  
- [ ] Simple UI with search and results
- [ ] Thumbnail display with links to NBA.com
- [ ] Search history (local storage)
- [ ] Legal disclaimer on all pages

### Phase 2: Enhanced Discovery
- [ ] Advanced NLP with context understanding
- [ ] Multiple link options (NBA.com, YouTube, etc.)
- [ ] User accounts and saved searches
- [ ] Social sharing of play discoveries
- [ ] Advanced filters (team, season, playoffs)

### Phase 3: Multi-Sport Expansion
- [ ] Abstract sport-agnostic architecture
- [ ] Add NFL, MLB, NHL official link providers
- [ ] Unified search across sports
- [ ] Sport-specific link generation

### Phase 4: AI Enhancement
- [ ] GPT integration for natural language responses
- [ ] Play pattern recognition
- [ ] Predictive search suggestions
- [ ] Personalized recommendations
- [ ] Play comparison tools

## Implementation Example

### Sample Search Flow (Link-Only)
```python
# User types: "show me all lebron dunks from last week"

# 1. EntityExtractor processes query
entities = entity_extractor.extract_entities(query)
# Result: {
#   "player": "LeBron James",
#   "player_id": "2544",
#   "action": "dunks",
#   "time_range": "last_week"
# }

# 2. SearchEngine queries nba_api for plays
plays = search_engine.get_plays_from_nba_api(entities)

# 3. For each play, get metadata and generate links
enhanced_results = []
for play in plays:
    # Get video metadata from nba_api
    video_event = videoevents.VideoEvents(
        game_id=play['GAME_ID'],
        game_event_id=play['EVENTNUM']
    )
    
    # Extract thumbnail for preview
    video_meta = video_event.get_dict()
    thumbnail = video_meta['resultSets']['Meta']['videoUrls'][0]['ltp']
    
    # Generate links to official sources
    enhanced_results.append({
        'play': play,
        'preview': {
            'thumbnail': thumbnail,
            'description': play['VISITORDESCRIPTION']
        },
        'watch_options': {
            'nba_com': f"https://www.nba.com/stats/events/?GameID={play['GAME_ID']}&GameEventID={play['EVENTNUM']}",
            'youtube_search': generate_youtube_search_url(play),
            'game_recap': f"https://www.nba.com/game/{play['GAME_ID']}"
        }
    })

# 4. Format and return results with links
return format_results_with_links(enhanced_results)
```

### Link Card Component (No Video Embedding)
```typescript
interface LinkCardProps {
    playData: {
        thumbnail: string;
        description: string;
        watchOptions: {
            nba_com: string;
            youtube_search: string;
            game_recap: string;
        };
    };
}

const LinkCard: React.FC<LinkCardProps> = ({ playData }) => {
    return (
        <div className="glass-panel rounded-lg overflow-hidden">
            {/* Thumbnail with overlay */}
            <div className="relative group cursor-pointer">
                <img 
                    src={playData.thumbnail} 
                    alt={playData.description}
                    className="w-full h-48 object-cover"
                />
                <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <svg className="w-16 h-16 text-white" /* play icon *//>
                </div>
            </div>
            
            {/* Description */}
            <div className="p-4">
                <p className="text-sm font-medium mb-3">{playData.description}</p>
                
                {/* External links */}
                <div className="flex flex-wrap gap-2">
                    <a 
                        href={playData.watchOptions.nba_com}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-blue-600 text-white px-3 py-1 rounded-full hover:bg-blue-700 transition"
                    >
                        NBA.com
                    </a>
                    <a 
                        href={playData.watchOptions.youtube_search}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-red-600 text-white px-3 py-1 rounded-full hover:bg-red-700 transition"
                    >
                        YouTube
                    </a>
                </div>
            </div>
        </div>
    );
};
```

## Security & Privacy

### Legal Compliance First
- **No Video Hosting**: PlayDex never stores or serves video files
- **Official Links Only**: All videos watched on NBA.com, YouTube, etc.
- **Terms of Service**: Full compliance with NBA and other leagues' policies
- **Copyright Respect**: Clear attribution and links to content owners
- **DMCA Safe Harbor**: As a search engine linking to official sources

### Technical Security
- Rate limiting on API endpoints to prevent abuse
- Thumbnail caching only (no video caching)
- Monitor NBA API usage to stay within limits
- DDoS protection with Cloudflare
- User privacy protection (no tracking of video views)

### User Agreement Template
```
By using PlayDex, you agree that:
- PlayDex is a search engine for discovering sports content
- All video content is owned by the respective leagues and broadcasters
- You will watch content only on official platforms
- PlayDex does not host, stream, or distribute any video content
```

## Monitoring & Analytics

### Search Analytics (Privacy-Focused)
- Popular search queries (anonymized)
- Entity extraction accuracy
- Search response times
- Link click-through rates (to official sources)

### API Health Monitoring
- NBA API availability and response times
- Rate limit usage tracking
- Thumbnail CDN performance
- Search indexing efficiency

### Legal Compliance Monitoring
- Regular ToS review for API providers
- Link validity checking
- Ensure no copyrighted content stored

## Getting Started

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/playdex

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend setup
cd ../frontend
npm install
npm run dev
```

### Environment Variables
```env
# Backend
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
NBA_API_KEY=... # If required

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_THUMBNAIL_CDN=... # For caching thumbnails only
```

### Legal Disclaimer Configuration
```typescript
// config/legal.ts
export const LEGAL_CONFIG = {
  disclaimer: "PlayDex is a search engine that helps you find official sports content. We do not host any videos.",
  terms_url: "/terms",
  privacy_url: "/privacy",
  show_on_each_result: true
};
```

## Contributing Guidelines
- Follow conventional commits
- Write comprehensive tests
- Document new features
- Performance benchmarks for new queries
- Accessibility standards (WCAG 2.1)

## Future Considerations
- Real-time game clip discovery
- Mobile app development
- Browser extension for quick searches
- API partnerships with leagues
- Premium features for power users
- Integration with fantasy sports platforms

---

## Summary

PlayDex is designed as a **search and discovery engine** for sports clips, not a video hosting platform. By linking to official sources only, we:

1. **Avoid copyright issues** - No video hosting or streaming
2. **Reduce infrastructure costs** - No video storage or bandwidth needs
3. **Stay legally compliant** - Respect content owners' rights
4. **Focus on core value** - Amazing search and discovery experience

The platform uses NBA's official API for metadata and generates links to official video sources, creating a legal, scalable way to help fans find the sports moments they're looking for.