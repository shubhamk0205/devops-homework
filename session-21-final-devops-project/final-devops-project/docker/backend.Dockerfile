# Backend image (FastAPI). Build context = application/
#   docker build -f docker/backend.Dockerfile -t helpdesk-backend:local application/
# python:3.13-alpine instead of python:3.12-slim (same lesson as session 17: the slim image had many HIGH CVEs)
FROM python:3.13-alpine

LABEL org.opencontainers.image.source="https://github.com/shubhamk0205/devops-homework"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt .

# install dependencies, then remove pip (not needed at runtime, and Trivy finds CVEs in it)
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip \
    && adduser -D -u 10001 appuser

COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app

# run as a normal user, not root
USER 10001
EXPOSE 8000

# 1) create/upgrade the database table  2) start the API
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
