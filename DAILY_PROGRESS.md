# Daily Progress

## 2026-04-28

### Completed

- Set up project scaffold for SkillSwap
- Added `docker-compose.yml` with:
  - nginx
  - identity-profile-service
  - session-service
  - notification-service
  - postgres
- Added Nginx gateway configuration
- Added PostgreSQL initialization script for service databases
- Built Identity & Profile Service foundation:
  - DB models
  - auth routes
  - profile routes
  - MFA routes
  - health endpoint
- Built Session Service foundation:
  - DB model
  - core session routes
  - status update route
  - health endpoint
- Built Notification Service foundation:
  - DB model
  - notification routes
  - health endpoint
- Added request ID middleware and basic structured logging in each service
- Built and started all containers successfully
- Verified all health endpoints
- Created GitHub repository: `Jeremiah-coding/SkillSwap`
- Added collaborator: `samiryehia`

### Next

- Sprint 2: centralized auth hardening across services
- Sprint 2: profile validation call from Session Service to Identity Service
- Sprint 2: notification call from Session Service to Notification Service
- Sprint 2: timeout/failure handling for inter-service calls
- Add tests and CI workflow

## 2026-05-06

### Completed

- Added automated pytest coverage for Identity & Profile Service:
  - auth register/login flow
  - TOTP setup/verify flow
  - protected `/api/v1/auth/me` endpoint
  - health endpoint
- Added automated pytest coverage for Session Service:
  - session creation flow
  - health endpoint
- Added automated pytest coverage for Notification Service:
  - notification creation flow
  - health endpoint
- Added GitHub Actions CI workflow at `.github/workflows/ci.yml`
  - runs on pull requests
  - runs on pushes to branches
  - executes service test suites as quality gate jobs
- Ran containerized test suites:
  - `identity-profile-service`: passing
  - `session-service`: passing
  - `notification-service`: passing

### Next

- Open Sprint 3 PR and request review from `samiryehia`
- Merge after CI passes and close linked Sprint 3 issues
