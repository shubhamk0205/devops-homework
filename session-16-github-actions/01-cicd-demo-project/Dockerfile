FROM python:3.13-alpine

# link the GHCR package to my repo
LABEL org.opencontainers.image.source="https://github.com/shubhamk0205/devops-homework"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV HOST=0.0.0.0 \
    PORT=5000

# run as a normal user, not root
RUN adduser -D appuser
USER appuser

EXPOSE 5000

CMD ["python", "-m", "app.app"]
