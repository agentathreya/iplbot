#!/bin/bash

echo "🏏 IPL Cricket Chatbot - Heroku Deployment Script"
echo "=" * 50

# Function to check if Heroku CLI is installed
check_heroku() {
    if ! command -v heroku &> /dev/null; then
        echo "❌ Heroku CLI not found. Please install it first:"
        echo "   curl https://cli-assets.heroku.com/install.sh | sh"
        exit 1
    fi
    echo "✅ Heroku CLI found"
}

# Function to deploy backend
deploy_backend() {
    echo "🖥️  Deploying Backend..."
    
    # Check if backend app exists
    if ! heroku apps:info ipl-cricket-backend >/dev/null 2>&1; then
        echo "Creating new backend app..."
        heroku create ipl-cricket-backend --region us
    fi
    
    # Set environment variables
    echo "Setting backend environment variables..."
    heroku config:set DATABASE_URL="$DATABASE_URL" -a ipl-cricket-backend
    heroku config:set GROQ_API_KEY="$GROQ_API_KEY" -a ipl-cricket-backend
    
    # Deploy using git subtree
    echo "Deploying backend code..."
    if ! git remote | grep -q heroku-backend; then
        heroku git:remote -a ipl-cricket-backend -r heroku-backend
    fi
    
    git subtree push --prefix=backend heroku-backend main
    
    echo "✅ Backend deployed to: https://ipl-cricket-backend.herokuapp.com"
}

# Function to deploy frontend
deploy_frontend() {
    echo "🌐 Deploying Frontend..."
    
    # Get backend URL
    BACKEND_URL="https://ipl-cricket-backend.herokuapp.com"
    
    # Check if frontend app exists
    if ! heroku apps:info ipl-cricket-frontend >/dev/null 2>&1; then
        echo "Creating new frontend app..."
        heroku create ipl-cricket-frontend --region us
    fi
    
    # Set environment variables
    echo "Setting frontend environment variables..."
    heroku config:set REACT_APP_API_URL="$BACKEND_URL" -a ipl-cricket-frontend
    
    # Deploy using git subtree
    echo "Deploying frontend code..."
    if ! git remote | grep -q heroku-frontend; then
        heroku git:remote -a ipl-cricket-frontend -r heroku-frontend
    fi
    
    git subtree push --prefix=frontend heroku-frontend main
    
    echo "✅ Frontend deployed to: https://ipl-cricket-frontend.herokuapp.com"
}

# Main deployment function
main() {
    # Check prerequisites
    check_heroku
    
    # Check if user is logged into Heroku
    if ! heroku auth:whoami >/dev/null 2>&1; then
        echo "Please login to Heroku first:"
        echo "   heroku login"
        exit 1
    fi
    
    # Check for environment variables
    if [[ -z "$DATABASE_URL" || -z "$GROQ_API_KEY" ]]; then
        echo "Please set environment variables:"
        echo "   export DATABASE_URL='your_database_url'"
        echo "   export GROQ_API_KEY='your_groq_key'"
        exit 1
    fi
    
    # Deploy both apps
    deploy_backend
    deploy_frontend
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "🌐 Frontend: https://ipl-cricket-frontend.herokuapp.com"
    echo "🖥️  Backend: https://ipl-cricket-backend.herokuapp.com"
    echo "📚 API Docs: https://ipl-cricket-backend.herokuapp.com/docs"
    echo ""
    echo "Test queries:"
    echo "- Kohli vs spin bowling"
    echo "- Best batting average vs spin min 500 runs"
    echo "- Top strike rate against pace bowling"
}

# Run main function
main "$@"