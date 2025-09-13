# ATS Analyzer - Development Guide

## Quick Start

```bash
# Start the entire development environment
./start-dev.sh

# Or manually with Docker Compose
cd infra && docker compose -f docker-compose.dev.yml up
```

## Project Structure

```
ATS/
├── frontend/           # Next.js 14 React application
│   ├── app/           # App router pages and layouts
│   ├── components/    # Reusable React components
│   ├── lib/          # Utilities and API client
│   ├── e2e/          # Playwright E2E tests
│   └── __tests__/    # Jest unit tests
├── backend/           # FastAPI Python application
│   ├── ats_analyzer/ # Main application package
│   │   ├── api/      # API routes and DTOs
│   │   ├── core/     # Configuration and logging
│   │   ├── services/ # Business logic services
│   │   ├── models/   # Database models
│   │   └── data/     # Static data files
│   ├── tests/        # Pytest unit tests
│   ├── migrations/   # Alembic database migrations
│   └── config/       # Configuration files
├── infra/            # Docker Compose and infrastructure
└── .github/          # CI/CD workflows
```

## Development Workflow

### Backend Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run tests
pytest -v

# Run linting
ruff check .
black --check .

# Start development server
./run_dev.sh
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Run tests
npm test
npm run e2e

# Generate API types from backend
npm run generate-types

# Build for production
npm run build
```

### Database Operations

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Connect to database
docker exec -it ats_postgres psql -U ats_user -d ats_db
```

## API Documentation

The backend automatically generates OpenAPI documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

#### POST /api/v1/parse
Parse résumé file and extract text with metadata.

**Request**: Multipart form with file upload
**Response**: 
```json
{
  "text": "extracted text content",
  "sections": {
    "summary": "...",
    "experience": "...",
    "education": "...",
    "skills": "..."
  },
  "meta": {
    "filetype": "pdf",
    "has_columns": false,
    "has_tables": false,
    "extractability_score": 0.92,
    "ocr_used": false
  }
}
```

#### POST /api/v1/analyze
Analyze résumé against job description.

**Request**:
```json
{
  "resume_text": "résumé content",
  "jd_text": "job description"
}
```

**Response**:
```json
{
  "score": {
    "overall": 78,
    "coverage": 72,
    "experience": 82,
    "education": 65
  },
  "missing": {
    "required": ["Docker", "PostgreSQL"],
    "preferred": ["AWS", "CI/CD"]
  },
  "weakly_supported": ["React"],
  "suggestions": [...],
  "ats": {
    "warnings": ["Multi-column layout detected"],
    "passes": ["Readable fonts", "Standard sections"]
  },
  "evidence": [...]
}
```

## Configuration

### Scoring Configuration

Edit `backend/config/scoring.yaml` to adjust scoring weights and thresholds:

```yaml
similarity_thresholds:
  required_hit: 0.75      # Minimum similarity for required skills
  preferred_hit: 0.75     # Minimum similarity for preferred skills
  weak_support: 0.65      # Threshold for weak skill support

weights:
  coverage: 0.6           # Weight for skill coverage score
  experience: 0.3         # Weight for experience score
  education: 0.1          # Weight for education score

section_weights:
  experience: 1.0         # Skills found in experience section
  projects: 0.8           # Skills found in projects section
  skills: 0.4             # Skills found in skills section
```

### Skills Taxonomy

Update `backend/ats_analyzer/data/skills_taxonomy.json` to add new skills:

```json
{
  "Programming Languages": {
    "Python": ["python", "py", "python3"],
    "JavaScript": ["javascript", "js", "node.js"]
  }
}
```

### Environment Variables

Create `.env` files for local development:

**Backend** (`backend/.env`):
```
DATABASE_URL=postgresql://ats_user:ats_pass@localhost:5432/ats_db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
UPLOAD_DIR=/tmp/ats_uploads
```

**Frontend** (`frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Testing

### Backend Tests

```bash
cd backend

# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=ats_analyzer --cov-report=html

# Specific test file
pytest tests/test_parse.py -v

# Test with database
pytest tests/ -v --tb=short
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm test

# E2E tests (requires running services)
npm run e2e

# E2E tests with UI
npm run e2e:ui

# Update snapshots
npm test -- -u
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3000, 8000, 5432, 6379 are free
2. **Docker issues**: Try `docker system prune` to clean up
3. **Database connection**: Wait for PostgreSQL to be ready
4. **spaCy model**: Run `python -m spacy download en_core_web_sm`
5. **Node modules**: Delete `node_modules` and run `npm install`

### Debugging

**Backend debugging**:
```bash
# View backend logs
docker compose -f infra/docker-compose.dev.yml logs -f backend

# Connect to backend container
docker exec -it ats_backend bash

# Run backend in debug mode
LOG_LEVEL=DEBUG ./run_dev.sh
```

**Frontend debugging**:
```bash
# View frontend logs
docker compose -f infra/docker-compose.dev.yml logs -f frontend

# Check build issues
npm run build

# Debug in browser
# Open http://localhost:3000 and use browser dev tools
```

### Performance Optimization

**Backend**:
- Use Redis for caching parsed documents
- Optimize database queries with indexes
- Profile with `cProfile` for bottlenecks

**Frontend**:
- Use React DevTools for component analysis
- Optimize bundle size with webpack-bundle-analyzer
- Implement proper loading states

## Deployment

### Production Build

```bash
# Backend
cd backend
docker build -t ats-analyzer-backend .

# Frontend
cd frontend
npm run build
docker build -t ats-analyzer-frontend .
```

### Environment Setup

For production deployment:

1. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
2. **Redis**: Use managed Redis (AWS ElastiCache, Redis Cloud)
3. **File Storage**: Use S3-compatible storage
4. **Monitoring**: Add application monitoring (Sentry, DataDog)
5. **SSL**: Configure HTTPS with proper certificates

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `npm test` and `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards

- **Python**: Follow PEP 8, use Black for formatting, Ruff for linting
- **TypeScript**: Follow ESLint rules, use Prettier for formatting
- **Commits**: Use conventional commit messages
- **Tests**: Maintain >80% code coverage
- **Documentation**: Update docs for new features
