# Base image changed from python:3.12-slim (44 HIGH CVEs in Debian packages, no fix available)
# to python:3.13-alpine (0 OS CVEs).
FROM python:3.13-alpine

# link the GHCR package to my repo
LABEL org.opencontainers.image.source="https://github.com/shubhamk0205/devops-homework"

WORKDIR /app

COPY requirements.txt .

# install the app dependencies, then remove pip itself:
# pip is not needed at runtime and Trivy found HIGH CVEs in the libraries bundled inside pip
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip

COPY app ./app

# run as a normal (non-root) user - k8s deployment has runAsNonRoot: true
RUN adduser -D -u 10001 appuser
USER 10001

ENV HOST=0.0.0.0 \
    PORT=5001

EXPOSE 5001

CMD ["python", "-m", "app.app"]
