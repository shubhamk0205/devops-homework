# Session 17 - Complete CI/CD & DevSecOps

## Task

Build a complete CI/CD + DevSecOps pipeline.
CI/CD: application build, unit testing, Docker image build, container registry, Kubernetes deployment.
Security: SAST, SCA, secret scanning, container image scanning, security gates.

Expected flow:
`Code -> Build -> Unit Test -> SAST -> SCA -> Secret Scan -> Docker Build -> Container Image Scan -> Security Gate -> Push Image -> Deploy to Kubernetes`

| # | Task | Folder |
|---|---|---|
| 01 | DevSecOps pipeline (Flask app, CodeQL, pip-audit, Gitleaks, Trivy, security gate, GHCR, kind) | [01-devsecops-pipeline](01-devsecops-pipeline) |

## Deliverables - where to find them

| Deliverable | Location |
|---|---|
| Application | [01-devsecops-pipeline/app](01-devsecops-pipeline/app), tests in [01-devsecops-pipeline/tests](01-devsecops-pipeline/tests) |
| Dockerfile | [01-devsecops-pipeline/Dockerfile](01-devsecops-pipeline/Dockerfile) |
| GitHub Actions workflow | active copy: [/.github/workflows/session-17-devsecops.yml](../.github/workflows/session-17-devsecops.yml), same file kept in [01-devsecops-pipeline/.github/workflows/devsecops.yml](01-devsecops-pipeline/.github/workflows/devsecops.yml) |
| Security tools configuration | [01-devsecops-pipeline/security/](01-devsecops-pipeline/security) (CodeQL, Gitleaks, Trivy) + gate policy in the workflow |
| Kubernetes manifests | [01-devsecops-pipeline/k8s/](01-devsecops-pipeline/k8s) |
| Successful pipeline output | [README section 7](01-devsecops-pipeline/README.md#7-successful-run-4---all-10-jobs-green) |
| Screenshots | [screenshots/](screenshots) |
| README | [01-devsecops-pipeline/README.md](01-devsecops-pipeline/README.md) |

The workflow lives at the repo root because GitHub only runs workflows from there. It has a `paths:` filter so it only
runs when `session-17-devsecops/` (or the workflow file) changes, and `workflow_dispatch` for manual runs.

## Result

| Run | Result | Reason |
|---|---|---|
| #1 | gate FAILED | real findings in the instructor's version: Flask debug mode (CodeQL) + 44 HIGH CVEs in `python:3.12-slim` (Trivy) |
| #2 | success | fixed: no debug mode, `python:3.13-alpine`, pip removed from runtime image, non-root user |
| #3 | gate FAILED | demo: a clearly fake hardcoded password, found by Gitleaks |
| #4 | success | fake password removed, deployed to kind |

Successful run: https://github.com/shubhamk0205/devops-homework/actions/runs/37672288885

![Successful run](screenshots/01-pipeline-success-summary.png)
