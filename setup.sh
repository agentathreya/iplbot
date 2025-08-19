#!/bin/bash

echo "🏏 Setting up IPL Cricket Chatbot..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete!"

# Setup frontend
cd ../frontend
echo "📦 Setting up frontend..."

# Install Node.js dependencies
npm install

echo "✅ Frontend setup complete!"

# Create environment files
cd ..
echo "⚙️  Creating environment files..."

# Backend .env
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "📝 Created backend/.env - Please add your GROQ_API_KEY"
fi

# Frontend .env
if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo "📝 Created frontend/.env"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your GROQ_API_KEY to backend/.env"
echo "2. Run the application with: ./run.sh"
echo ""
echo "For manual setup:"
echo "Backend: cd backend && source venv/bin/activate && python main.py"
echo "Frontend: cd frontend && npm start"