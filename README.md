# Todo App

Full-stack task management application. This repository contains both the backend and frontend as a monorepo.

## Repository Structure

```
todo_app/
├── backend/    # REST API — FastAPI + SQLAlchemy + SQLite
└── frontend/   # SPA — Angular 21
```

Each folder contains its own `README.md` with detailed information about the stack, project structure, environment variables, and step-by-step setup instructions:

- [`backend/README.md`](./backend/README.md) — FastAPI API setup and configuration
- [`frontend/README.md`](./frontend/README.md) — Angular app setup and configuration

## Backend

REST API built with **FastAPI**, handling authentication (JWT) and task management. See [`backend/README.md`](./backend/README.md) for setup and run instructions.

**Quick start:**
```bash
cd backend
source ./venv/bin/activate
uvicorn app.main:app --reload
```

API available at `http://127.0.0.1:8000` — interactive docs at `http://127.0.0.1:8000/docs`.

## Frontend

Single-page application built with **Angular 21**, communicating with the backend API via a local dev proxy. See [`frontend/README.md`](./frontend/README.md) for setup and run instructions.

**Quick start:**
```bash
cd frontend
ng serve
```

App available at `http://localhost:4200`.

## Running the Full Stack

Start both servers in separate terminals:

```bash
# Terminal 1 — Backend
cd backend
source ./venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend
ng serve
```

Open `http://localhost:4200` in your browser.
