# CI/CD Runbook

## Overview
This project uses GitHub Actions for CI and image publishing, Docker Hub for container registry, Railway for backend runtime, and Vercel for frontend hosting.

## GitHub Actions
- `.github/workflows/ci-backend.yml`
  - PR/push → main, only when `backend/**` changes: run backend tests and perform a Docker build check (no push)
- `.github/workflows/ci-frontend.yml`
  - PR/push → main, only when `frontend/**` changes: run frontend lint and unit tests
- `.github/workflows/release.yml`
  - push tag `v*`: run tests, then build and push Docker images tagged `latest`, `<git-sha>`, and `<tag>`

### Required Secrets
- `DOCKERHUB_USERNAME`: Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub PAT

Images default to `guillhermmzenni/sdd-todo-challange`. Change the `IMAGE_REPO` env in the release workflow if needed.

## Docker Image
- Context: `backend/`
- Dockerfile: `backend/Dockerfile`
- Exposes port `8000`
- Entrypoint: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Railway (Backend)
1. Create a new service from Docker image: `guillhermmzenni/sdd-todo-challange:latest`
2. Configure environment variables:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `CORS_ORIGINS` (include your Vercel domain)
3. Deploy or re-deploy as needed; for immutable releases, use tag images (e.g., `v1.0.0` or specific SHA).

## Vercel (Frontend)
1. Connect repo to Vercel
2. Set env vars:
   - `API_BASE_URL` → Railway backend URL (e.g., `https://<railway-domain>`)
3. Vercel will auto-deploy previews for PRs and production on `main`.

## Release Flow
1. Create a tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
2. GitHub Actions builds and publishes images with: `latest`, `<git-sha>`, and `vX.Y.Z`
3. Update Railway to pull `vX.Y.Z` if pinning to immutable releases.

