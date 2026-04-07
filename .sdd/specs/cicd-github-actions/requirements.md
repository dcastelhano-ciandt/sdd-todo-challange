# Requirements (CI/CD with GitHub Actions, Docker, Vercel, Railway)

## Goals
- Provide automated CI on pull requests and `main` for both backend and frontend, with scoped workflows that run only when relevant paths change.
- Provide CD for backend via container images pushed to Docker Hub with two tags: `latest` and a unique immutable tag (git SHA or timestamp).
- Provide CD for frontend through Vercel auto-deploys connected to GitHub, with proper environment configuration to reach the backend.
- Prefer deploying from new Git tags for “release” builds.

## Scope
- CI: run backend unit/integration tests and frontend unit/E2E tests on PRs and on pushes to `main`, each in split workflows (backend-only or frontend-only) based on path filters. Enforce type-check + Prettier check as lint gate.
- Build and publish backend Docker images only on Git tag pushes; CI (PR/main) builds image to validate but does not push.
- Coordinate environment variables between services (API base URL, secrets).
- Document manual Railway deployment workflow consuming the pushed Docker image.
- Ensure reproducibility and traceability with immutable tags.

## Non-Goals
- Provisioning cloud infrastructure via IaC.
- Managing database migrations in production environments (handled by app lifecycle per existing backend design).

## Functional Requirements
1. CI triggers
   - On PRs targeting `main`: run tests in split workflows (backend-only or frontend-only) based on path filters; do not publish images.
   - On push to `main`: run tests in split workflows (backend-only or frontend-only) based on path filters; do not publish images.
   - On Git tag push (`v*`): run tests; publish Docker image with `latest` and the tag/Git SHA.
2. Backend CI steps
   - Install Python deps; run unit + integration tests.
   - Build container image using repository `Dockerfile`.
3. Frontend CI steps
   - Install Node deps; run lint/unit tests (and optional E2E where feasible in CI).
   - Lint runs `npm run lint` which performs `tsc --noEmit` and `prettier -c` for `src/**/*`. Prototype assets under `src/ui/**` are ignored via `.prettierignore`.
4. Docker image publishing
   - Push to public Docker Hub repo `DOCKERHUB_ORG/PROJECT` with tags: `latest` and `<git-sha>` (and `<git-tag>` when building from tag).
   - Authenticate via GitHub Actions secrets.
5. Environment and configuration
   - Backend: secrets and config via Railway dashboard (manual), not stored in repo.
   - Frontend: `API_BASE_URL` provided via Vercel env vars; production build points to deployed backend.
6. Release/tag strategy
   - Creating a semver tag `vX.Y.Z` triggers a release build and image tagged `vX.Y.Z` and `latest`.
7. Documentation
   - Provide short runbooks for: setting up repo secrets, connecting Vercel, deploying on Railway using the Docker image, tag-based release flow.

## Quality Requirements
- Workflows must complete within reasonable time with caching (node_modules/pip caches).
- Idempotent and reproducible builds; immutable tags used for traceability.
- Least-privilege secrets usage (scoped Docker Hub credentials).

