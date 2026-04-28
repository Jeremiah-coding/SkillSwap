# SkillSwap

SkillSwap is a microservices-based backend for a peer skill-exchange platform.

## Architecture

- Nginx API Gateway
- Identity & Profile Service (FastAPI)
- Session Service (FastAPI)
- Notification Service (FastAPI)
- PostgreSQL

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Pydantic
- Docker Compose
- Nginx

## Current Sprint Status

Sprint 1 foundations are in place:

- Repository scaffolded
- Dockerfiles created for all services
- Docker Compose created
- PostgreSQL configured and running
- Identity & Profile Service scaffolded
- Session Service scaffolded
- Notification Service scaffolded
- Health endpoints available in all services

## Project Structure

- `identity-profile-service/`
- `session-service/`
- `notification-service/`
- `nginx/`
- `docker-compose.yml`
- `init-db.sql`

## Run Locally

```bash
docker compose up --build -d
```

Service health endpoints:

- `http://localhost:8001/health`
- `http://localhost:8002/health`
- `http://localhost:8003/health`

Gateway entrypoint:

- `http://localhost`
