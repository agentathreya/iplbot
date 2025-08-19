#!/bin/bash

echo "🏏 Starting IPL Cricket Chatbot..."

# Check if environment files exist
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found. Run ./setup.sh first."
    exit 1
fi

if [ ! -f "frontend/.env" ]; then
    echo "❌ Frontend .env file not found. Run ./setup.sh first."
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start backend
echo "🚀 Starting backend server..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🚀 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Servers started!"
echo "🔗 Backend API: http://localhost:8000"
echo "🔗 Frontend App: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait