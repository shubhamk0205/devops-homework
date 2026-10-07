# Session 16 - CI/CD & GitHub Actions

## Task

Build a complete CI/CD demo project using GitHub Actions (reference: instructor's `10-final-cicd-pipeline`).
It should cover: CI vs CD, CI/CD pipeline, GitHub Actions, Workflow, Jobs, Steps, Runners, Secrets, Artifacts, Build, Test, Pipeline execution.

| # | Task | Folder |
|---|---|---|
| 01 | CI/CD demo project (Flask app + pytest + Docker + GitHub Actions CI and CD) | [01-cicd-demo-project](01-cicd-demo-project) |

## Deliverables - where to find them

| Deliverable | Location |
|---|---|
| Application source code | [01-cicd-demo-project/app](01-cicd-demo-project/app), tests in [01-cicd-demo-project/tests](01-cicd-demo-project/tests) |
| Dockerfile | [01-cicd-demo-project/Dockerfile](01-cicd-demo-project/Dockerfile) |
| GitHub Actions workflow | active copy: [/.github/workflows/session-16-ci-cd.yml](../.github/workflows/session-16-ci-cd.yml), same file kept in [01-cicd-demo-project/.github/workflows/ci-cd.yml](01-cicd-demo-project/.github/workflows/ci-cd.yml) |
| CI pipeline | jobs `CI - Test`, `CI - Build`, `CI - Docker Build` |
| CD pipeline | jobs `CD - Push Image to GHCR`, `CD - Deploy to Staging (runner)` |
| Screenshots of successful pipeline execution | [screenshots/](screenshots) |
| README | [01-cicd-demo-project/README.md](01-cicd-demo-project/README.md) |

Why is the workflow at the repo root? GitHub Actions only reads workflows from `.github/workflows/` at the root of the repository.
The workflow uses a `paths:` filter so it only runs when files in `session-16-github-actions/` (or the workflow itself) change.

## Pipeline at a glance

```text
push to main ──> CI - Test ──┬──> CI - Build ────────┬──> CD - Push Image to GHCR ──> CD - Deploy to Staging
                             └──> CI - Docker Build ─┘
```

Successful run: https://github.com/shubhamk0205/devops-homework/actions/runs/37685570866

![Successful run](screenshots/01-pipeline-success-summary.png)
