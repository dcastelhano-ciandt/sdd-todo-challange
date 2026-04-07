# Implementation Plan

- [ ] 1. Create split CI workflows
  - `.github/workflows/ci-backend.yml`
    - Trigger on PR/push to `main` with paths filter for `backend/**`
    - Jobs: backend tests; Docker build check (no push)
  - `.github/workflows/ci-frontend.yml`
    - Trigger on PR/push to `main` with paths filter for `frontend/**`
    - Jobs: lint and unit tests

- [ ] 2. Create GitHub Actions workflow for releases (`.github/workflows/release.yml`)
  - Trigger on tags matching `v*`
  - Re-run tests as in CI
  - Build and push Docker with tags: `latest`, `${{ github.sha }}`, `${{ github.ref_name }}`

- [ ] 3. Prepare Docker build context
  - Ensure backend `backend/Dockerfile` exists and builds the FastAPI app
  - Verify image exposes correct port and runs the server (e.g., uvicorn)

- [ ] 4. Configure GitHub repo secrets
  - Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (PAT)
  - Optionally add `DOCKERHUB_ORG` and `DOCKERHUB_REPO`

- [ ] 5. Vercel setup
  - Connect repo to Vercel
  - Set `API_BASE_URL` env var for Production/Preview to Railway backend URL(s)
  - Verify builds deploy on `main` and PRs (preview)

- [ ] 6. Railway deployment runbook
  - Document creating a service from `DOCKERHUB_ORG/PROJECT:latest`
  - List required env vars (SECRET_KEY, DATABASE_URL, CORS origin for Vercel domain)
  - Note release flow: tag `vX.Y.Z` for immutable deploy image

- [ ] 7. Lint/format policy
  - Ensure `frontend/package.json` defines `lint`, `lint:types`, `lint:format` per design
  - Ensure `.prettierignore` excludes `src/ui/**`
  - CI must fail on formatting drift; contributors run `npm run format` locally

- [ ] 8. Optional: docs
  - Add `docs/ci-cd.md` summarizing workflows, secrets, and release process

