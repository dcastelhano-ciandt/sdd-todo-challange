# Frontend Environment Configuration

This app reads its API base URL from a generated `public/env.js` file at runtime.

## Quick start (local)
1. Copy `.env.example` to `.env` and set:
   - `API_BASE_URL=http://localhost:8000`
2. Generate env and start:
   - `npm install`
   - `npm run start` (runs `npm run build:env` then `ng serve`)

## Build
- `npm run build` runs `npm run build:env` first, then `ng build`.

## How it works
- `scripts/generate-env.mjs` reads `.env` and writes `public/env.js`:
  - `window.ENV = { API_BASE_URL: "<value>" }`
- `src/index.html` includes `/env.js` before boot, making `window.ENV` available.
- API services call relative endpoints when `API_BASE_URL` is empty.

## Vercel
1. In Vercel project settings, add an environment variable:
   - `API_BASE_URL=https://<your-railway-service>.up.railway.app`
2. Add a build command step (or Framework preset command override) to generate env.js before build:
   - `npm ci && npm run build:env && npm run build`
3. Deploy. The app will call the backend using `API_BASE_URL`.

# Todo App — Frontend

SPA built with **Angular 21**, using standalone components, reactive forms, signals, and an HTTP interceptor for JWT authentication.

## Tech Stack

| Layer | Library |
|---|---|
| Framework | Angular 21 |
| Language | TypeScript 5.9 |
| State | Angular Signals |
| Forms | Reactive Forms + NgModel |
| HTTP | Angular HttpClient + Interceptors |
| Unit Tests | Vitest |
| E2E Tests | Playwright |
| Formatter | Prettier |

## Project Structure

```
frontend/src/app/
├── auth/
│   ├── guards/         # Route guard (redirects unauthenticated users)
│   ├── interceptors/   # JWT injection + 401 redirect
│   ├── services/       # AuthApiService, AuthStateService (token storage)
│   └── login/          # Login page component
│   └── register/       # Register page component
├── tasks/
│   ├── services/       # TaskApiService, TaskStateService (signals)
│   ├── task-list/      # Task list page (create, filter)
│   └── task-item/      # Individual task row (edit, toggle, delete)
├── shared/
│   └── models/         # TypeScript interfaces (Task, Auth)
├── app.routes.ts       # Route definitions
├── app.config.ts       # App-level providers
└── styles.css          # Global design tokens and component styles
```

## Routes

| Path | Component | Protected |
|---|---|---|
| `/login` | LoginComponent | No |
| `/register` | RegisterComponent | No |
| `/tasks` | TaskListComponent | Yes (authGuard) |

## API Proxy (Development)

Requests to `/api/*` are proxied to `http://127.0.0.1:8000` via `proxy.conf.json`, so no CORS issues during local development. Make sure the backend is running before starting the frontend.

## How to Run

**1. Navigate to the frontend folder**
```bash
cd frontend
```

**2. Install dependencies**
```bash
npm install
```

**3. Start the development server**
```bash
ng serve
```

The app will be available at `http://localhost:4200`.

## Running Tests

**Unit tests (Vitest)**
```bash
ng test
```

**End-to-end tests (Playwright)**
```bash
ng e2e
```

## Build

```bash
ng build
```

Output is placed in the `dist/` directory, optimized for production.
