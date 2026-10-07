# Session 13 - Kubernetes Storage, HPA & Probes

All tasks were done on minikube (docker driver, Kubernetes v1.37, metrics-server addon enabled). Every output in the READMEs is copied from my terminal.

| Task | Folder | What I did |
|------|--------|------------|
| 1. Kubernetes Volumes | [01-kubernetes-volumes](01-kubernetes-volumes/README.md) | Notes + hands-on for emptyDir, hostPath, PV, PVC, StorageClass and dynamic provisioning |
| 2. HPA Hands-on | [02-hpa](02-hpa/README.md) | Deployed nginx, configured `hpa.yml`, ran a load generator, watched CPU and Pods scale 1 -> 5 -> 1 |
| 3. Mini Project | [03-mini-project](03-mini-project/README.md) | Web app with PVC + HPA + startup/readiness/liveness probes in namespace `production-webapp` |

## Deliverables checklist

| Deliverable | Where |
|-------------|-------|
| Volume documentation | `01-kubernetes-volumes/README.md` (+ example YAMLs in the same folder) |
| HPA YAML | `02-hpa/hpa.yml` |
| Load generator | `02-hpa/load-generator.yaml` |
| HPA output | `02-hpa/README.md` (steps 3-8) |
| Screenshots | `screenshots/` |
| Mini-project implementation | `03-mini-project/*.yaml` |
| README documentation | this file + one README per task |

## Screenshots

| File | Shows |
|------|-------|
| `screenshots/hpa-watch.png` | `kubectl get hpa -w` for the whole Task 2 test (scale up and down) |
| `screenshots/hpa-under-load.png` | HPA at 5 replicas, `kubectl top pods` under load |
| `screenshots/mini-project-web-service.png` | nginx page through `web-service` (port-forward) |
| `screenshots/mini-project-hpa-watch.png` | mini project HPA scaling 2 -> 4 -> 2 |

(The terminal screenshots are the real command output rendered as images.)
