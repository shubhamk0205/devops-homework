# Session 15: Helm

In this session I practised Helm, the package manager for Kubernetes, on my local minikube cluster.
All work was done in the `helm-demo` namespace, which I deleted at the end.

```text
Helm v4.3.0 | minikube (Kubernetes v1.37, docker driver) | macOS arm64
```

## Tasks

| # | Task | Folder | What is inside |
|---|---|---|---|
| 1 | Helm Commands | [01-helm-commands](01-helm-commands/) | `helm create` chart (`myapp/`) + README with create, install, list, status, get, upgrade, history, rollback, uninstall, repo, search |
| 2 | Helm Rollback | [02-helm-rollback](02-helm-rollback/) | Install -> Upgrade -> Verify -> Upgrade again (bad) -> Verify -> Rollback -> Verify |
| 3 | Mini Project | [03-mini-project](03-mini-project/) | `notes-chart/` (Chart.yaml, values.yaml, values-prod.yaml, templates) installed, upgraded, broken and rolled back |

Screenshots are in [screenshots/](screenshots/).

## Deliverables checklist

| Deliverable | Where |
|---|---|
| Helm chart | [01-helm-commands/myapp](01-helm-commands/myapp/), [03-mini-project/notes-chart](03-mini-project/notes-chart/) |
| values.yaml | [notes-chart/values.yaml](03-mini-project/notes-chart/values.yaml), [notes-chart/values-prod.yaml](03-mini-project/notes-chart/values-prod.yaml) |
| Templates | [notes-chart/templates](03-mini-project/notes-chart/templates/) |
| Installation | Task 1 step 2, Task 2 step 1, Task 3 step 3 |
| Upgrade | Task 1 step 6, Task 2 steps 2 and 4, Task 3 steps 4 and 5 |
| Rollback | Task 1 step 8, Task 2 step 6, Task 3 step 6 |
| Screenshots | [screenshots/notes-dev-v1.png](screenshots/notes-dev-v1.png) |
| README files | this file + one README per task |
| Mini project | [03-mini-project](03-mini-project/) |

## Helm in one picture

```text
          Chart                          Release (in cluster)
   +-------------------+           +-----------------------------+
   | Chart.yaml        |  install  | revision 1  (Install)       |
   | values.yaml       | --------> | revision 2  (Upgrade)       |
   | templates/*.yaml  |  upgrade  | revision 3  (Upgrade)       |
   +-------------------+ --------> | revision 4  (Rollback to 2) |
            ^                      +-----------------------------+
            |                                    |
     -f values-prod.yaml                         v
     --set key=value               Deployment / Service / ConfigMap
```

## What I learned overall

- A chart is a template package, values make it reusable for different environments.
- Every install/upgrade/rollback is a numbered revision, so I always have a history of what changed.
- Rollback creates a new revision instead of deleting history.
- Helm says `deployed` as soon as Kubernetes accepts the YAML; to be sure the app is healthy use `--wait` or check the pods.
