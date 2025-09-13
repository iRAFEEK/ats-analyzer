# ATS Analyzer Infrastructure

This directory contains Docker Compose configuration for running the ATS Analyzer in development mode.

## Quick Start

```bash
# Start all services
docker compose -f docker-compose.dev.yml up

# Start with Celery workers (optional)
docker compose -f docker-compose.dev.yml --profile celery up

# Start in background
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Stop services
docker compose -f docker-compose.dev.yml down
```

## Services

### Core Services
- **postgres** (port 5432) - PostgreSQL database
- **redis** (port 6379) - Redis for caching and queues
- **backend** (port 8000) - FastAPI backend service
- **frontend** (port 3000) - Next.js frontend application

### Optional Services (--profile celery)
- **celery-worker** - Background task processing
- **flower** (port 5555) - Celery monitoring dashboard

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Flower (if enabled): http://localhost:5555

## Development

### Hot Reload
Both frontend and backend support hot reload:
- Backend: Changes to Python files trigger automatic reload
- Frontend: Changes to React/TypeScript files trigger automatic rebuild

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it ats_postgres psql -U ats_user -d ats_db

# Run migrations
docker exec -it ats_backend alembic upgrade head
```

### Logs
```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
```

### Cleanup
```bash
# Stop and remove containers
docker compose -f docker-compose.dev.yml down

# Remove volumes (WARNING: deletes all data)
docker compose -f docker-compose.dev.yml down -v

# Remove images
docker compose -f docker-compose.dev.yml down --rmi all
```

## Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `UPLOAD_DIR` - Directory for file uploads

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NODE_ENV` - Environment (development, production)

## Troubleshooting

### Common Issues

1. **Port conflicts**: Make sure ports 3000, 5432, 6379, 8000 are available
2. **Permission issues**: Ensure Docker has permission to bind volumes
3. **Build failures**: Run `docker compose build --no-cache` to rebuild images
4. **Database connection**: Wait for PostgreSQL to be ready (health checks handle this)

### Health Checks
All services include health checks. Use `docker compose ps` to see service status.

### Reset Everything
```bash
# Nuclear option - removes everything
docker compose -f docker-compose.dev.yml down -v --rmi all
docker system prune -a
```
