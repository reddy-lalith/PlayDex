#!/bin/bash

echo "Setting up PlayDex development environment..."

# Backend setup
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created backend/.env - Please update with your configuration"
fi

# Frontend setup
echo "Setting up frontend..."
cd ../frontend

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    cp .env.example .env.local
    echo "Created frontend/.env.local - Please update with your configuration"
fi

echo "Setup complete!"
echo ""
echo "To start the development servers:"
echo "Backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "Frontend: cd frontend && npm run dev"