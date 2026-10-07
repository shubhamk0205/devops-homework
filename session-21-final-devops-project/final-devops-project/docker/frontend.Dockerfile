# Frontend image (React + Vite) - multi-stage build. Build context = application/
#   docker build -f docker/frontend.Dockerfile -t helpdesk-frontend:local application/

# ---- stage 1: build the static files with Node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund
COPY frontend/ .
RUN npm run build

# ---- stage 2: serve them with nginx (non-root image, listens on 8080) ----
FROM nginxinc/nginx-unprivileged:1.31-alpine
LABEL org.opencontainers.image.source="https://github.com/shubhamk0205/devops-homework"
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_URL=http://backend:8000
EXPOSE 8080
