# PlayDex - AI Sports Search Engine

PlayDex is an AI-powered sports search engine that allows users to search for specific sports clips using natural language queries. The interface mirrors the clean, conversational experience of Claude and ChatGPT.

**Important**: PlayDex does NOT host any video content. It serves as an intelligent search and discovery layer that connects users to official video sources.

## Features

- 🔍 Natural language search for sports moments
- 💬 Claude/ChatGPT-like conversational interface
- 🏀 NBA play-by-play data integration
- 🔗 Links to official video sources only
- 📱 Responsive, glassmorphic design
- ⚡ Fast, intelligent search results

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React

### Backend
- FastAPI (Python)
- nba_api
- PostgreSQL
- Redis

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL
- Redis

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/playdex.git
cd playdex
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd ../frontend
npm install
```

4. Configure environment variables:
- Copy `.env.example` to `.env` in both frontend and backend directories
- Update with your configuration

5. Run the development servers:

Backend:
```bash
cd backend
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm run dev
```

## Legal Notice

PlayDex is a search engine that helps you discover official sports content. We do not host any videos. All video content is property of the respective leagues and broadcasters.

## License

MIT License - see LICENSE file for details