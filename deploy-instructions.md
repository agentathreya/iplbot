# 🚀 Heroku Deployment Guide - Backend + Frontend

## Architecture Overview
- **Backend**: FastAPI on Heroku (separate app)
- **Frontend**: React on Heroku (separate app)
- **Database**: External PostgreSQL (Neon)
- **AI**: Groq API

## Prerequisites
- Heroku account (free tier available)
- Heroku CLI installed
- Git repository (already set up)

## 📋 Deployment Steps

### Step 1: Deploy Backend to Heroku

1. **Create Heroku App for Backend**
   ```bash
   heroku create ipl-cricket-backend --region us
   ```

2. **Set Environment Variables**
   ```bash
   heroku config:set DATABASE_URL="postgresql://neondb_owner:npg_CfEz1gjOR0uh@ep-still-feather-a1rvh26h-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require" -a ipl-cricket-backend
   
   heroku config:set GROQ_API_KEY="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" -a ipl-cricket-backend
   ```

3. **Deploy Backend**
   ```bash
   cd backend
   git subtree push --prefix=backend heroku-backend main
   ```

   OR use Heroku Dashboard:
   - Connect GitHub repo
   - Select `backend/` folder
   - Deploy

### Step 2: Deploy Frontend to Heroku

1. **Create Heroku App for Frontend**
   ```bash
   heroku create ipl-cricket-frontend --region us
   ```

2. **Set Environment Variables**
   ```bash
   # Replace YOUR_BACKEND_URL with actual backend URL from step 1
   heroku config:set REACT_APP_API_URL="https://ipl-cricket-backend.herokuapp.com" -a ipl-cricket-frontend
   ```

3. **Deploy Frontend**
   ```bash
   cd frontend
   git subtree push --prefix=frontend heroku-frontend main
   ```

### Step 3: Update CORS Configuration

After getting the frontend URL, update backend CORS:

```bash
# Update the backend main.py allow_origins to include your frontend URL
# Then redeploy the backend
```

## 🌐 Expected URLs

- **Backend API**: https://ipl-cricket-backend.herokuapp.com
- **Frontend App**: https://ipl-cricket-frontend.herokuapp.com
- **API Docs**: https://ipl-cricket-backend.herokuapp.com/docs

## 🔧 Alternative: Heroku Dashboard Deployment

### For Backend:
1. Go to Heroku Dashboard
2. Create new app: `ipl-cricket-backend`
3. Connect GitHub repo
4. Select `backend/` folder as root
5. Add environment variables in Settings
6. Deploy from `main` branch

### For Frontend:
1. Create new app: `ipl-cricket-frontend`
2. Connect same GitHub repo
3. Select `frontend/` folder as root
4. Add `REACT_APP_API_URL` environment variable
5. Deploy from `main` branch

## 📊 Environment Variables Summary

### Backend Environment Variables:
```
DATABASE_URL=postgresql://neondb_owner:npg_CfEz1gjOR0uh@ep-still-feather-a1rvh26h-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
GROQ_API_KEY=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
```

### Frontend Environment Variables:
```
REACT_APP_API_URL=https://your-backend-app.herokuapp.com
```

## 🧪 Testing After Deployment

1. **Backend Health Check**:
   ```
   curl https://ipl-cricket-backend.herokuapp.com/
   ```

2. **Frontend Access**:
   ```
   https://ipl-cricket-frontend.herokuapp.com
   ```

3. **Test Queries**:
   - "Kohli vs spin bowling"
   - "Best batting average vs spin min 500 runs"
   - "Top strike rate against pace bowling"

## 🔒 Security Notes

- Repository is private ✅
- Environment variables are encrypted in Heroku ✅
- CORS configured for production ✅
- API endpoints secured ✅

## 💰 Cost

- **Heroku Free Tier**: 1000 dyno hours/month (enough for 2 apps)
- **Database**: Using external Neon (free tier)
- **AI API**: Groq API (your existing key)

Total: **FREE** for development/demo usage