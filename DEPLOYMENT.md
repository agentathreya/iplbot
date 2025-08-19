# 🚀 Streamlit Deployment Guide

## Quick Deploy Steps

### 1. Deploy Backend (Railway/Render/Heroku)

#### Option A: Railway (Recommended)
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Select the `backend` folder as the root
4. Set environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `GROQ_API_KEY`: Your Groq API key
5. Deploy automatically!

#### Option B: Render
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repo
4. Set build command: `cd backend && pip install -r requirements.txt`
5. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables
7. Deploy!

### 2. Deploy Streamlit Frontend

#### Streamlit Cloud (Free)
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select repository: `agentathreya/iplchatbot`
4. Main file path: `streamlit_app.py`
5. Add secrets in Settings:
   ```toml
   BACKEND_URL = "https://your-backend-url.com"
   ```
6. Click Deploy!

### 3. Environment Variables Needed

#### Backend (.env)
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
GROQ_API_KEY=gsk_your_groq_api_key_here
```

#### Streamlit Secrets (secrets.toml)
```
BACKEND_URL = "https://your-backend-url.com"
```

## Alternative: Complete Streamlit App

You can also run everything in Streamlit by:
1. Converting FastAPI backend to Streamlit functions
2. Using st.cache for database connections
3. Deploying single Streamlit app

## Database Setup

### Option 1: Use Existing Database
- Keep your existing PostgreSQL with 277K records
- Update connection string in environment variables

### Option 2: Upload to New Database
1. Export data from your current database
2. Create new PostgreSQL instance (Neon, Supabase, Railway)
3. Import the data using the upload script

## Testing Deployment

1. Visit your Streamlit app URL
2. Test example queries:
   - "Top 10 run scorers in IPL"
   - "MS Dhoni career stats"
   - "Best bowlers in death overs"

## Troubleshooting

### Common Issues:
- **Connection Error**: Check BACKEND_URL in Streamlit secrets
- **API Timeout**: Increase timeout in requests calls
- **Database Error**: Verify DATABASE_URL is correct

### Debug Steps:
1. Check Streamlit logs for errors
2. Test backend API endpoints directly
3. Verify environment variables are set correctly

## Cost Estimation

- **Streamlit Cloud**: Free tier available
- **Railway**: $5/month for backend hosting
- **Database**: $0-20/month depending on provider
- **Total**: $5-25/month for full deployment

## Support

Visit the GitHub repository for issues and updates:
https://github.com/agentathreya/iplchatbot

Happy Cricket Analytics! 🏏
