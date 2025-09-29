"""
Health check endpoint for County Health Data API
Vercel serverless function implementation.

This implementation was created with assistance from Claude AI (Anthropic).
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="County Health Data API", version="1.0.0")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "County Health Data API is running"}

# For Vercel serverless functions
def handler(request, response):
    """Vercel handler"""
    return app(request, response)