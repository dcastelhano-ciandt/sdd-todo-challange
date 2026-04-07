# Design (CI/CD with GitHub Actions, Docker Hub, Vercel, Railway)

## Overview
Introduce three GitHub Actions workflows:
- `ci-backend.yml`: Runs on PRs to `main` and on pushes to `main`, only when `backend/**` changes. Executes backend tests and performs a Docker build check (no push).
- `ci-frontend.yml`: Runs on PRs to `main` and on pushes to `main`, only when `frontend/**` changes. Executes frontend lint and unit tests.
- `release.yml`: Runs on Git tag pushes (`v*`). Executes tests and publishes Docker images with `latest` and immutable tags.

Backend container images are published to Docker Hub. Railway deployment is manual but consumes the published image. Vercel connects to the GitHub repo and builds/deploys the frontend; environment variables point to the backend URL.

## Workflows
### ci-backend.yml
- Triggers:
  - `pull_request` to `main` with paths: `backend/**`, `.github/workflows/ci-backend.yml`
  - `push` to `main` with paths: `backend/**`, `.github/workflows/ci-backend.yml`
- Jobs:
  - Tests:
    - Python 3.11, cache pip, install `backend/requirements.txt`, run pytest (unit + integration)
  - Docker build check:
    - Build the backend image using `backend/Dockerfile` without pushing (validates build)

### ci-frontend.yml
- Triggers:
  - `pull_request` to `main` with paths: `frontend/**`, `.github/workflows/ci-frontend.yml`
  - `push` to `main` with paths: `frontend/**`, `.github/workflows/ci-frontend.yml`
- Jobs:
  - Lint and tests:
    - Node 20, npm cache, `npm ci`, `npm run lint`, and `npm test`
    - Lint contract:
      - `npm run lint:types` → `tsc -p tsconfig.app.json --noEmit`
      - `npm run lint:format` → `prettier -c "src/**/*.{ts,html,css,scss,json,md}"`
      - `.prettierignore` excludes `src/ui/**` prototypes from format checks

### release.yml
- Triggers:
  - `push` tags: `v*`
- Jobs:
  - Re-run backend and frontend tests
  - Build and push Docker
    - Tags: `latest`, `${{ github.sha }}`, and the tag ref name (e.g., `v1.2.3`)

## Tagging Strategy
- Publish images only on tag builds; do not push on PR/main CI.
- Immutable tags:
  - Git SHA: `${{ github.sha }}`
  - On tag builds: also `${{ github.ref_name }}` (e.g., `v1.2.3`)

## Repository and Paths
- Backend lives in `backend/` (FastAPI, Python). If different, adjust paths.
- Frontend lives in `frontend/` (Angular). If different, adjust paths.
- Dockerfile at repo root or `backend/` depending on final build context; assume backend Dockerfile is at `backend/Dockerfile`.

## Secrets and Configuration
- GitHub Actions repo secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN` (PAT)
  - Optional: `DOCKERHUB_ORG` and `DOCKERHUB_REPO` (or encode in workflow)
- Vercel project:
  - Set `API_BASE_URL` pointing to Railway deployment URL
  - Connect the repo, auto-deploy on `main` and on PR previews
- Railway service:
  - Create service from Docker image `DOCKERHUB_ORG/PROJECT:latest`
  - Configure env vars (SECRET_KEY, DB URL, CORS origin for Vercel domain, etc.)

## Developer Experience
- Tag-based release flow: create `vX.Y.Z` tag to produce immutable image tag and align Vercel production deployments.
- Documentation included in repo under `docs/ci-cd.md` (optional follow-up).

