# Session 20: Monitoring, Observability & GitOps

In this session I set up monitoring for a small app on minikube with Prometheus + Grafana, wrote down the three pillars of
observability, and did a GitOps demo where Argo CD deploys an app from this GitHub repo.

```text
minikube (Kubernetes v1.37, docker driver) | Helm v4.3.0 | kube-prometheus-stack | Argo CD v3.5.4
Namespaces used: monitoring, monitoring-demo, argocd, gitops-demo (all deleted at the end)
```

## Tasks

| # | Task | Folder | What is inside |
|---|---|---|---|
| 1 | Monitoring | [01-monitoring](01-monitoring/) | Helm values for kube-prometheus-stack, demo app with probes, PrometheusRule. Metrics, logs, alerts, CPU, memory, app health |
| 2 | Observability | [02-observability](02-observability/) | Metrics / logs / traces, why observability, common tools, Kubernetes observability |
| 3 | GitOps | [03-gitops](03-gitops/) | Argo CD Application + `app/` manifests watched from GitHub, auto-sync on Git change, self-heal |

## Deliverables checklist

| Deliverable | Where |
|---|---|
| Monitoring demo | [01-monitoring/README.md](01-monitoring/README.md) |
| Observability documentation | [02-observability/README.md](02-observability/README.md) |
| GitOps demo | [03-gitops/README.md](03-gitops/README.md) |
| Screenshots | [screenshots/](screenshots/) (list below) |
| README.md | this file + one per task |

Screenshots:

| File | Shows |
|---|---|
| [prometheus-alerts-firing.png](screenshots/prometheus-alerts-firing.png) | My `demo-app.rules` with DemoAppHighCPU and DemoAppReplicasUnavailable firing |
| [prometheus-cpu-query.png](screenshots/prometheus-cpu-query.png) | PromQL CPU graph per pod (spike to the 0.5 core limit) |
| [grafana-namespace-pods.png](screenshots/grafana-namespace-pods.png) | Grafana namespace dashboard: CPU + memory per pod |
| [grafana-pod-cpu-memory.png](screenshots/grafana-pod-cpu-memory.png) | Grafana pod dashboard: CPU vs request/limit, throttling |
| [argocd-app-synced-2-replicas.png](screenshots/argocd-app-synced-2-replicas.png) | Argo CD app first sync, 2 pods |
| [argocd-app-synced-3-replicas.png](screenshots/argocd-app-synced-3-replicas.png) | After the Git commit "Scale session20-mini to three replicas" |
| [argocd-app-image-1.28.png](screenshots/argocd-app-image-1.28.png) | After the image change commit (new ReplicaSet) |

## Big picture

```text
                 MONITORING / OBSERVABILITY                         GITOPS

   app pods --metrics--> Prometheus --> Grafana          developer --git push--> GitHub repo
      |                     |                                                        |
      +--logs--> kubectl logs   +--> alert rules --> Alertmanager                 Argo CD (pulls)
                                                                                     |
                                                                          compare + sync + self-heal
                                                                                     |
                                                                                 Kubernetes
```

## Final mental model

```text
METRICS -> numbers          PROMETHEUS -> collects metrics + alert rules
LOGS    -> events           GRAFANA    -> dashboards
TRACES  -> request journey  ALERTMANAGER -> sends alerts

GIT        -> desired state
ARGO CD    -> reconciliation
KUBERNETES -> actual state
```

## What I learned overall

- Prometheus + Grafana give history and alerts on top of what `kubectl top/logs/describe` gives right now.
- Alerts need a condition and a `for` time; I saw them go pending -> firing -> resolved.
- In GitOps, Git is the only way to change the cluster; Argo CD synced my commits and reverted my manual `kubectl scale`.
