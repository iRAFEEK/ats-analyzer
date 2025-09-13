#!/bin/bash
set -e

# Load environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DATABASE_URL="${DATABASE_URL:-postgresql://ats_user:ats_pass@localhost:5432/ats_db}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

# Download spaCy model if not exists
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || python -m spacy download en_core_web_sm

# Run database migrations
alembic upgrade head

# Start the FastAPI server
uvicorn ats_analyzer.main:app --host 0.0.0.0 --port 8000 --reload
