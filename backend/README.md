# Todo App — Backend

REST API built with **FastAPI**, **SQLAlchemy**, and **SQLite**, following a layered architecture (routers → services → repositories → models).

## Tech Stack

| Layer | Library |
|---|---|
| Framework | FastAPI 0.111 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic 1.13 |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Server | Uvicorn |
| Tests | Pytest + pytest-asyncio |

## Project Structure

```
backend/
├── app/
│   ├── core/           # Settings and custom exceptions
│   ├── models/         # SQLAlchemy models (User, Task, TokenBlacklist)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── repositories/   # Database access layer
│   ├── services/       # Business logic (auth, tasks)
│   ├── routers/        # HTTP route handlers (auth, tasks)
│   ├── dependencies.py # FastAPI dependencies (current user, DB session)
│   └── main.py         # App entry point, CORS, exception handlers
├── alembic/            # Database migrations
├── tests/              # Test suite
└── requirements.txt
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Authenticate and receive JWT |
| GET | `/api/v1/tasks` | List tasks (optional `?status=pending\|completed`) |
| POST | `/api/v1/tasks` | Create task |
| PUT | `/api/v1/tasks/{id}` | Update task title |
| PATCH | `/api/v1/tasks/{id}/toggle` | Toggle task completion |
| DELETE | `/api/v1/tasks/{id}` | Delete task |

Interactive docs available at `http://127.0.0.1:8000/docs` once the server is running.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production-32-chars!!` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiry |
| `DATABASE_URL` | `sqlite:///./todo.db` | SQLAlchemy connection string |
| `CORS_ORIGIN` | `http://localhost:4200` | Allowed frontend origin |

Copy `.env.example` to `.env` and adjust as needed.

## How to Run

**1. Navigate to the backend folder**
```bash
cd backend
```

**2. Create a virtual environment (if it doesn't exist yet)**
```bash
python -m venv venv
```

**3. Activate the virtual environment**
```bash
source ./venv/bin/activate
```

**4. Install dependencies (first time or after updating requirements.txt)**
```bash
pip install -r requirements.txt
```

**5. Apply database migrations (first time or after new migrations)**
```bash
alembic upgrade head
```

**6. Start the development server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Running Tests

```bash
pytest
```
