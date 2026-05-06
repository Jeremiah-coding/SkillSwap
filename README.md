# SkillSwap – FastAPI Microservices with Nginx Gateway

SkillSwap is a peer skill-exchange microservices platform where users create profiles, request learning sessions, and receive notifications when session events occur. The system implements proper microservices architecture with an Nginx API gateway, centralized authentication, request ID propagation, and structured logging.

## Project Overview

This is **not a task manager**. This is a peer mentoring/skill exchange microservices system.

**Example use cases:**
- A user offers Python mentoring
- Another user offers UI design coaching  
- A user requests a session with a mentor
- The session is approved, rejected, or cancelled
- Notifications are created for these events
- All requests pass through the Nginx gateway
- All protected routes use centralized auth and role-based access

## Architecture

The system consists of 5 components:

1. **Nginx API Gateway** (port 80) – Routes all client requests to appropriate services
2. **Identity & Profile Service** (port 8001) – Centralized authentication, JWT issuance, user/profile management
3. **Session Service** (port 8002) – Session request management, validation, status tracking
4. **Notification Service** (port 8003) – Notification storage and retrieval
5. **PostgreSQL Database** – Shared instance with separate databases per service

All communication between services goes through HTTP calls with explicit timeouts and failure handling.

## Tech Stack

- **FastAPI** – Async web framework for all microservices
- **PostgreSQL** – Relational database with separate databases per service
- **SQLAlchemy** – Async ORM for database operations
- **Pydantic** – Data validation and settings management
- **Docker Compose** – Local development orchestration
- **Nginx** – Reverse proxy and API gateway
- **pytest + pytest-asyncio** – Automated testing
- **GitHub Actions** – CI/CD pipeline

## Service Boundaries

### 1. Identity & Profile Service

**Responsibilities:**
- User registration and login
- JWT access token and refresh token issuance
- TOTP MFA setup, verification, and disable
- User/profile creation and updates
- Role ownership and management
- Profile lookup endpoints for other services (both public and internal)

**Key Features:**
- Centralized authentication authority for the system
- Password hashing with bcrypt
- JWT-based access control with role claims
- TOTP MFA demo implementation
- Protected routes for profile and auth management
- Internal endpoint for service-to-service profile validation (no JWT required)

**Database:** `identity_profiles_db`

### 2. Session Service

**Responsibilities:**
- Creating session requests between users
- Listing and retrieving sessions
- Approving, rejecting, and cancelling sessions
- Filtering sessions by status
- Validating profile existence through Identity Service HTTP calls
- Calling Notification Service when major session events occur

**Key Features:**
- Does NOT directly access profile tables
- Validates all profiles through HTTP calls to Identity Service
- Implements explicit timeouts for inter-service calls
- Handles downstream service failures gracefully
- Calls Notification Service on: session_created, session_approved, session_rejected, session_cancelled

**Database:** `sessions_db`

### 3. Notification Service

**Responsibilities:**
- Creating notification records
- Listing and retrieving notifications
- Filtering notifications by profile_id
- Storing notification delivery status

**Key Features:**
- Receives real service-to-service calls from Session Service
- Tracks notification type (e.g., session_requested, session_approved)
- Stores notification status (e.g., unread, read)
- Not a placeholder – used in the actual session flow

**Database:** `notifications_db`

## How Authentication Works

1. **Registration**: User creates account with username, email, and password
   - Password is hashed using bcrypt before storage
   - User role defaults to "member" unless specified as "admin"

2. **Login**: User submits credentials
   - Identity Service validates password hash
   - Returns access token (expires in 30 minutes) and refresh token (expires in 7 days)
   - Both are JWTs signed with shared SECRET_KEY

3. **Authorization**: Protected routes require JWT in `Authorization: Bearer <token>` header
   - Token contains user ID and role claims
   - Role-based access control checks role for admin-only endpoints
   - Access tokens are short-lived; refresh tokens renew them

4. **Refresh Token Flow**: Access tokens expire after 30 minutes
   - Client submits refresh token to `/api/v1/auth/refresh`
   - Identity Service issues new access token without requiring credentials

## How TOTP MFA Works

1. **Setup** (`POST /api/v1/mfa/setup`):
   - Identity Service generates a TOTP secret using pyotp
   - Returns secret and QR code URI for authenticator apps (Google Authenticator, Authy, etc.)
   - User scans QR code or enters secret manually

2. **Verification** (`POST /api/v1/mfa/verify`):
   - User provides 6-digit code from authenticator app
   - Identity Service validates using pyotp.TOTP
   - Enables TOTP flag on user account if valid

3. **Disable** (`POST /api/v1/mfa/disable`):
   - User provides 6-digit code to confirm identity
   - Identity Service validates and disables TOTP

**Important**: TOTP is optional – users can login without it, but if enabled, the code must be verified during login (handled by client).

## How Request IDs Are Propagated

Request ID tracking ensures end-to-end visibility across all services.

1. **Nginx**: Adds `X-Request-ID` header if not present
   - `add_header X-Request-ID $request_id always;`
   - Sets it in the proxy header: `proxy_set_header X-Request-ID $request_id;`

2. **Each Service**: RequestIDMiddleware (in `app/middleware/request_id.py`)
   - Extracts request ID from incoming `X-Request-ID` header
   - If missing, generates a new UUID
   - Stores in `request.state.request_id`
   - Logs request details with the ID
   - Returns ID in response `X-Request-ID` header

3. **Service-to-Service Calls**: HTTP clients forward the request ID
   - Session Service includes `X-Request-ID` header when calling Identity Service
   - Session Service includes `X-Request-ID` header when calling Notification Service
   - All services log with request_id for cross-service tracing

4. **Structured Logging Format**:
   ```
   request_id=<uuid> method=<METHOD> path=<PATH> status=<STATUS> duration_ms=<TIME>
   ```

## How the End-to-End Session Flow Works

When a user creates a session request, this flow occurs:

1. Client sends `POST /api/v1/sessions` to Nginx with JWT in Authorization header
2. Nginx routes to Session Service, forwarding request ID
3. Session Service validates JWT/authorization
4. Session Service makes HTTP call to Identity Service:
   - `GET /api/v1/profiles/<requester_profile_id>` (with timeout)
   - `GET /api/v1/profiles/<mentor_profile_id>` (with timeout)
   - Both calls include `X-Request-ID` header
5. If profiles don't exist, Session Service returns 422 error
6. Session Service saves session to database with "pending" status
7. Session Service makes HTTP call to Notification Service:
   - `POST /api/v1/notifications` with session_created event
   - Includes `X-Request-ID` header
8. Notification Service creates notification records
9. If Notification Service fails, Session Service logs but returns success (session already saved)
10. All involved services logged the same request ID

## API Route Summary

### Identity & Profile Service (`/api/v1/`)

**Authentication:**
- `POST /api/v1/auth/register` – Create new user account
- `POST /api/v1/auth/login` – Login and get access/refresh tokens
- `POST /api/v1/auth/refresh` – Refresh expired access token
- `GET /api/v1/auth/me` – Get current authenticated user info

**MFA:**
- `POST /api/v1/mfa/setup` – Generate TOTP secret and QR code
- `POST /api/v1/mfa/verify` – Verify TOTP code and enable MFA
- `POST /api/v1/mfa/disable` – Disable TOTP MFA for user

**Profiles:**
- `POST /api/v1/profiles` – Create profile for authenticated user
- `GET /api/v1/profiles` – List all active profiles
- `GET /api/v1/profiles/{profile_id}` – Get specific profile (public and internal)
- `PATCH /api/v1/profiles/{profile_id}` – Update profile (auth required)

**Health:**
- `GET /health` – Service health check

### Session Service (`/api/v1/`)

- `POST /api/v1/sessions` – Create session request (validates profiles with Identity Service)
- `GET /api/v1/sessions` – List sessions (with optional `?status=<status>` filter)
- `GET /api/v1/sessions/{session_id}` – Get specific session
- `PATCH /api/v1/sessions/{session_id}/status` – Update session status (calls Notification Service)
- `GET /health` – Service health check

**Session Statuses:** pending, approved, rejected, cancelled

### Notification Service (`/api/v1/`)

- `POST /api/v1/notifications` – Create notification (called by Session Service)
- `GET /api/v1/notifications` – List all notifications
- `GET /api/v1/notifications/profile/{profile_id}` – Get notifications for specific user
- `GET /health` – Service health check

## Nginx Routing Summary

All client requests enter through Nginx on port 80. Nginx routes based on URL path:

```
/api/v1/auth/*        → Identity & Profile Service :8000
/api/v1/mfa/*         → Identity & Profile Service :8000
/api/v1/profiles/*    → Identity & Profile Service :8000
/api/v1/sessions/*    → Session Service :8000
/api/v1/notifications/* → Notification Service :8000
```

**Request Flow:**
1. Client sends request to `http://localhost/api/v1/sessions`
2. Nginx receives request, generates/preserves `X-Request-ID`
3. Nginx proxies to `http://session-service:8000/api/v1/sessions`
4. Session Service processes and responds
5. Response includes `X-Request-ID` header back to client

**Service-to-Service Calls:**
- Session Service calls `http://identity-profile-service:8000/api/v1/profiles/{id}` with timeout
- Session Service calls `http://notification-service:8000/api/v1/notifications` with timeout
- All calls include `X-Request-ID` header for distributed tracing

## Database Structure

PostgreSQL container runs with 3 separate databases (service ownership):

1. **identity_profiles_db**
   - `users` table – user accounts, passwords, TOTP secrets, roles
   - `profiles` table – user profiles with skills and preferences

2. **sessions_db**
   - `sessions` table – session requests between users

3. **notifications_db**
   - `notifications` table – notification records for events

Each service has its own connection string and only accesses its own database.

## How to Run Locally

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)

### Start the System

```bash
# Clone repository
git clone https://github.com/Jeremiah-coding/SkillSwap.git
cd SkillSwap

# Start all services with Docker Compose
docker compose up --build -d
```

This will:
- Build Docker images for all 3 services
- Start Nginx on port 80
- Start Identity Service on port 8001
- Start Session Service on port 8002
- Start Notification Service on port 8003
- Start PostgreSQL on port 5432
- Create all 3 databases
- Run all services with environment variables configured

### Verify Services Are Running

```bash
# Check all containers
docker compose ps

# Test Gateway
curl http://localhost/health  # Should fail (route not found) – expected

# Test service health endpoints directly
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### Stop the System

```bash
docker compose down
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f identity-profile-service
docker compose logs -f session-service
docker compose logs -f notification-service
```

## Testing Instructions

### Run All Tests

```bash
# Run tests for all services
docker compose up --build -d

# In another terminal, run pytest for each service
cd identity-profile-service && python -m pytest -v && cd ..
cd session-service && python -m pytest -v && cd ..
cd notification-service && python -m pytest -v && cd ..
```

### Run Tests for Specific Service

```bash
cd identity-profile-service
python -m pytest -v                              # All tests
python -m pytest tests/test_auth.py -v           # Auth tests only
python -m pytest tests/test_mfa.py -v            # MFA tests only
python -m pytest tests/test_protected.py -v      # Protected endpoint tests
python -m pytest -k "register" -v                # Tests matching "register"
```

### Test Coverage

**Identity & Profile Service Tests:**
- ✅ User registration flow
- ✅ User login flow
- ✅ TOTP setup flow
- ✅ TOTP verification flow
- ✅ Protected `/api/v1/auth/me` endpoint
- ✅ Health endpoint
- ✅ Failure cases (invalid credentials, duplicate username, etc.)

**Session Service Tests:**
- ✅ Session creation flow
- ✅ Health endpoint

**Notification Service Tests:**
- ✅ Notification creation flow
- ✅ Health endpoint

## CI/CD Summary

### GitHub Actions Pipeline

The project includes a CI/CD workflow at `.github/workflows/ci.yml` that:

**Triggers:**
- On pull requests to any branch
- On pushes to any branch

**Jobs:**
- `identity-tests` – Runs pytest suite for Identity & Profile Service
- `session-tests` – Runs pytest suite for Session Service
- `notification-tests` – Runs pytest suite for Notification Service

**Quality Gate:**
- All 3 test suites must pass
- If any service tests fail, the CI pipeline fails
- Pull requests cannot be merged without passing CI

**Environment:**
- Python 3.12
- SQLite database for testing (isolated from production DB)
- Dependencies installed from each service's `requirements.txt`

### Current Status

- ✅ Sprint 1 Complete: Service foundations, Docker setup, basic endpoints
- ✅ Sprint 2 Complete: Gateway routing, centralized auth, inter-service communication, request ID propagation, timeout handling
- ✅ Sprint 3 Complete: Automated tests, GitHub Actions CI/CD pipeline, quality gate enforcement

All CI checks are passing. See `.github/workflows/ci.yml` for details.

## Known Limitations & Future Work

1. **TOTP MFA is demo only** – Not enforced during login (client-side responsibility)
2. **No refresh token rotation** – Tokens don't expire after use
3. **No rate limiting** – Requests are not throttled
4. **No API versioning beyond /api/v1** – Future versions would need new routes
5. **No service-to-service authentication** – Services trust each other (would use mTLS in production)
6. **No database migrations** – Uses SQLAlchemy ORM to manage schema
7. **No container registry** – Images built locally only
8. **No horizontal scaling** – Services run as single instances

## Project Structure

```
skillswap/
├── docker-compose.yml           # Docker Compose orchestration
├── nginx/
│   └── nginx.conf              # Nginx gateway config
├── identity-profile-service/
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── config.py           # Settings
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── core/               # Auth, security, dependencies
│   │   ├── middleware/         # Request ID middleware
│   │   ├── models/             # User, Profile models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── routers/            # Auth, profiles, MFA endpoints
│   ├── tests/                  # Pytest test suites
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile
├── session-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── core/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── routers/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── notification-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── core/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── routers/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions pipeline
├── README.md                   # This file
└── DAILY_PROGRESS.md           # Development progress tracking
```

## Git Workflow

- All work on feature branches (e.g., `feature/auth-mfa`, `feature/session-integration`)
- Commits are incremental and follow `type(scope): description` format
- Pull requests start as Draft, become Ready for Review when complete
- Main branch protection requires 1 approval and passing CI before merge
- No direct pushes to main

## Contributing

This project follows a strict Git workflow:
1. Create feature branch from main
2. Make incremental commits
3. Open Draft PR immediately
4. Push commits as work progresses
5. Convert to Ready for Review when scope is complete
6. Request review from `samiryehia`
7. Merge after approval and CI pass

For details, see `.github/workflows/ci.yml` and Git workflow settings in repository.
