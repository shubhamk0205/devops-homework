# Session 21: Final DevOps Project & Troubleshooting

In this session I built one end-to-end DevOps project that uses everything from the course: a small HelpDesk ticket
app (FastAPI + React + PostgreSQL) that goes through GitHub Actions (build, test, SAST, SCA, secret scan, Docker build,
image scan, security gate, push to GHCR, deploy to Kubernetes with Helm, GitOps update), runs on minikube through
Argo CD, is monitored with Prometheus + Grafana, has its cloud infrastructure in Terraform, and has a troubleshooting
challenge with 5 faults that I broke on purpose and fixed.

```text
Application -> Git -> GitHub -> CI Pipeline -> Build & Test -> Security Scanning -> Docker Image
            -> Container Registry -> Kubernetes -> Helm -> Monitoring -> GitOps
```

| Part | Where |
|---|---|
| Full project + README | [final-devops-project/](final-devops-project/) -> [README.md](final-devops-project/README.md) |
| Application | [final-devops-project/application](final-devops-project/application/) |
| Docker | [final-devops-project/docker](final-devops-project/docker/) |
| Kubernetes + troubleshooting | [final-devops-project/kubernetes](final-devops-project/kubernetes/) |
| Helm chart | [final-devops-project/helm/helpdesk](final-devops-project/helm/helpdesk/) |
| Terraform | [final-devops-project/terraform](final-devops-project/terraform/) |
| CI/CD workflow | [/.github/workflows/session-21-final.yml](../.github/workflows/session-21-final.yml) (active), copy in [final-devops-project/.github/workflows](final-devops-project/.github/workflows/) |
| Security configs | [final-devops-project/security](final-devops-project/security/) |
| Monitoring | [final-devops-project/monitoring](final-devops-project/monitoring/) |
| GitOps | [final-devops-project/gitops](final-devops-project/gitops/) |
| Screenshots | [final-devops-project/screenshots](final-devops-project/screenshots/) |

Pipeline run: [37689794443](https://github.com/shubhamk0205/devops-homework/actions/runs/37689794443) - all 11 jobs passed,
the GitOps job committed tag `4c001a7` and Argo CD synced it to minikube (Synced / Healthy).

Note: GitHub only runs workflows from the repo root `.github/workflows/`, so the root file is the one that runs.
