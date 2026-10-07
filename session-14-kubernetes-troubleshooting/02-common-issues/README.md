# Task 2 - Troubleshoot Common Issues

For every issue I made a `broken.yaml`, deployed it on minikube, and then followed the same 6 steps:

```text
 1. Identify  ->  2. Investigate  ->  3. Root cause  ->  4. Fix  ->  5. Verify  ->  6. Document
 (get)           (describe/events/      (one sentence)    (fixed.yaml)  (get/logs/exec)   (README)
                  logs/exec)
```

| # | Issue | What I saw | Key command | Root cause | Fix |
|---|-------|-----------|-------------|-----------|-----|
| 1 | [CrashLoopBackOff](01-crashloopbackoff/README.md) | `CrashLoopBackOff`, restarts growing, exit code 1 | `kubectl logs --previous` | `DATABASE_URL` env var missing, app exits | add `env` |
| 2 | [ImagePullBackOff](02-imagepullbackoff/README.md) | `ImagePullBackOff`, 0 restarts | `kubectl describe pod` (events) | tag typo `nginx:1.277` -> `not found` | `nginx:1.27` |
| 3 | [ErrImagePull](03-errimagepull/README.md) | `ErrImagePull` right after create | `kubectl describe pod` (events) | registry host doesn't exist -> `no such host` | use `docker.io/library/nginx:1.27` |
| 4 | [Pending](04-pending/README.md) | `Pending`, NODE `<none>` | `kubectl describe pod` + `describe node` | requests 500 CPU / 1000Gi > node | realistic requests |
| 5 | [ContainerCreating](05-containercreating/README.md) | stuck `ContainerCreating` | `kubectl describe pod` (`FailedMount`) | Secret `db-credentials` not created | create the Secret |
| 6 | [Service connectivity](06-service-connectivity/README.md) | `Connection refused` via Service | `kubectl describe svc` (Endpoints :8080) | `targetPort: 8080`, app on 80 | `targetPort: 80` |
| 7 | [DNS](07-dns-issues/README.md) | `bad address 'orders-svc'` | `kubectl exec -- nslookup` | wrong Service name (NXDOMAIN) | `orders-api.default.svc.cluster.local` |
| 8 | [Pod networking](08-pod-networking/README.md) | Pod IP `Connection refused`, ping OK | `kubectl exec -- netstat -tln` | app bound to `127.0.0.1` | bind `0.0.0.0` |
| 9 | [Configuration](09-configuration-issues/README.md) | `CreateContainerConfigError` | `kubectl describe pod` (events) | ConfigMap key `APP_MODE` vs `app_mode` | correct key |

## Which command to start with (my cheat sheet)

```text
 STATUS                         FIRST LOOK AT
 ------                         -------------
 CrashLoopBackOff / Error   ->  kubectl logs <pod> --previous, exit code in describe
 ImagePullBackOff/ErrImage  ->  describe -> Events "Failed to pull image ..."
 Pending                    ->  describe -> Events "FailedScheduling ..."
 ContainerCreating (long)   ->  describe -> Events "FailedMount / FailedCreatePodSandBox"
 CreateContainerConfigError ->  describe -> Events "couldn't find key / configmap not found"
 Running but not working    ->  describe svc / get endpoints / exec curl / nslookup / netstat
```

All resources were created in the `default` namespace and deleted after each issue.
