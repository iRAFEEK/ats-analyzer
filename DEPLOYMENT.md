# ATS Résumé Analyzer - Deployment Guide

## Deploying to Vercel

This application can be deployed to Vercel as a full-stack application with both the Next.js frontend and FastAPI backend.

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to a GitHub repository
3. **OpenAI API Key**: Get your API key from [OpenAI](https://platform.openai.com/api-keys)

### Deployment Steps

#### 1. Prepare Your Repository

Make sure your code is pushed to a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/ats-analyzer.git
git push -u origin main
```

#### 2. Connect to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will automatically detect it's a Next.js project

#### 3. Configure Environment Variables

In your Vercel project dashboard, go to Settings > Environment Variables and add:

**Required:**
- `OPENAI_API_KEY` = Your OpenAI API key

**Optional:**
- `DATABASE_URL` = PostgreSQL connection string (if using external DB)
- `DEBUG` = `false`
- `LOG_LEVEL` = `INFO`
- `CORS_ORIGINS` = `https://your-domain.vercel.app`

#### 4. Deploy

Click "Deploy" and Vercel will:
- Build the Next.js frontend
- Set up the FastAPI backend as serverless functions
- Configure routing between frontend and backend

### Project Structure for Vercel

```
/
├── vercel.json              # Vercel configuration
├── requirements.txt         # Python dependencies
├── runtime.txt             # Python version
├── backend/
│   ├── main.py             # Entry point for Vercel
│   └── ats_analyzer/       # Your FastAPI app
└── frontend/               # Next.js app
    ├── package.json
    └── next.config.mjs
```

### Important Notes

#### Backend Considerations

1. **Cold Starts**: Serverless functions have cold start delays (~2-3 seconds)
2. **Timeout**: Functions timeout after 30 seconds (configurable in vercel.json)
3. **Memory**: Limited to 1GB RAM on free tier
4. **File Size**: Large ML models might cause deployment issues

#### Database Options

1. **SQLite** (default): Works for development, stored in serverless function
2. **PostgreSQL**: Recommended for production (use Vercel Postgres or external service)
3. **Vercel Postgres**: Native integration, easy to set up

#### Performance Optimizations

1. **Model Loading**: Consider caching ML models between requests
2. **Database**: Use connection pooling for external databases
3. **File Processing**: Optimize document parsing for serverless environment

### Alternative Deployment Options

#### Option 1: Frontend on Vercel, Backend on Railway/Render

1. Deploy frontend to Vercel (remove backend from vercel.json)
2. Deploy backend to Railway or Render
3. Update `NEXT_PUBLIC_API_URL` in frontend to point to backend URL

#### Option 2: Full Stack on Railway

1. Use Railway for both frontend and backend
2. Better for long-running processes and larger ML models
3. More predictable pricing for compute-heavy workloads

### Troubleshooting

#### Common Issues

1. **Import Errors**: Ensure all Python dependencies are in requirements.txt
2. **Model Download Failures**: Pre-download spaCy models in build process
3. **Memory Issues**: Reduce model sizes or use external model hosting
4. **Cold Start Timeouts**: Implement health check endpoints

#### Debug Deployment

1. Check Vercel Function logs in dashboard
2. Test API endpoints directly: `https://your-app.vercel.app/api/v1/health`
3. Monitor function execution time and memory usage

### Production Checklist

- [ ] Environment variables configured
- [ ] OpenAI API key added
- [ ] Database connection tested
- [ ] CORS origins updated
- [ ] Error monitoring set up
- [ ] Performance testing completed
- [ ] Security headers configured

### Support

For deployment issues:
1. Check Vercel documentation
2. Review function logs
3. Test locally with production environment variables
