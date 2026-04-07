FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app \
    PORT=8000

WORKDIR ${APP_HOME}

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ${APP_HOME}/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# App source
COPY app ${APP_HOME}/app
COPY alembic.ini ${APP_HOME}/alembic.ini
COPY alembic ${APP_HOME}/alembic

EXPOSE ${PORT}

CMD sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'

