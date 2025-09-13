"""Main entry point for Vercel deployment."""

from ats_analyzer.main import app

# Vercel expects the app to be available at the module level
# This file serves as the entry point for serverless deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
