# Issue 1 - CrashLoopBackOff

**Problem statement:** A Python app Pod (`crashloop-pod`) keeps restarting and never becomes Ready.

**Files:** `broken.yaml` (the problem), `fixed.yaml` (the solution)

`CrashLoopBackOff` means: the container starts, then **exits/crashes**, kubelet restarts it, it crashes again... and kubelet waits longer each time (10s, 20s, 40s ... up to 5 min) before the next restart. The "BackOff" is that waiting.

```text
 start -> crash (exit 1) -> wait 10s -> start -> crash -> wait 20s -> start -> crash -> wait 40s ...
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pod crashloop-pod
```
```text
pod/crashloop-pod created
NAME            READY   STATUS   RESTARTS      AGE
crashloop-pod   0/1     Error    3 (27s ago)   49s
```
A bit later:
```text
NAME            READY   STATUS             RESTARTS      AGE
crashloop-pod   0/1     CrashLoopBackOff   4 (79s ago)   2m58s
```
What I observed: `READY 0/1`, the restart count keeps going up and the status switches between `Error` (it just crashed) and `CrashLoopBackOff` (waiting before the next restart).

## 2. Investigate

```bash
kubectl describe pod crashloop-pod
```
```text
Containers:
  python-app:
    Image:         python:3.11-alpine
    ...
    State:          Terminated
      Reason:       Error
      Exit Code:    1
      Started:      Thu, 08 Oct 2026 00:56:20 +0530
      Finished:     Thu, 08 Oct 2026 00:56:20 +0530
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
      Started:      Thu, 08 Oct 2026 00:55:55 +0530
      Finished:     Thu, 08 Oct 2026 00:55:55 +0530
    Ready:          False
    Restart Count:  3
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  49s               default-scheduler  Successfully assigned default/crashloop-pod to minikube
  Normal   Pulling    48s               kubelet            Pulling image "python:3.11-alpine"
  Normal   Pulled     39s               kubelet            Successfully pulled image "python:3.11-alpine" in 9.896s (9.896s including waiting). Image size: 23808448 bytes.
  Normal   Created    2s (x4 over 38s)  kubelet            Container created
  Normal   Started    2s (x4 over 38s)  kubelet            Container started
  Normal   Pulled     2s (x3 over 38s)  kubelet            Container image "python:3.11-alpine" already present on machine and can be accessed by the pod
  Warning  BackOff    1s (x4 over 37s)  kubelet            Back-off restarting failed container python-app in pod crashloop-pod_default(02d53f82-c9ec-410e-badb-b61ad60fa152)
```
What I observed: the image pulled fine and the container **started**, but it finished in the same second with **Exit Code 1**. So Kubernetes is OK - the app itself is failing. Next step = logs.

```bash
kubectl logs crashloop-pod
kubectl logs crashloop-pod --previous
```
```text
[FATAL ERROR]: DATABASE_URL environment variable is MISSING!

[FATAL ERROR]: DATABASE_URL environment variable is MISSING!
```
(`--previous` shows the logs of the last crashed container. When I first ran it right after a restart it said `unable to retrieve container logs`, because that old container had just been removed - running it again during the BackOff wait worked.)

## 3. Root cause

The application needs the `DATABASE_URL` environment variable. The Pod spec has no `env:` section, so the app prints a fatal error and exits with code 1. Kubernetes restarts it (restartPolicy `Always`) and it fails again in a loop.

## 4. Fix

Add the missing environment variable (`fixed.yaml`):
```yaml
      env:
        - name: DATABASE_URL
          value: "postgres://db-service:5432/appdb"
```
Env vars of a running Pod cannot be changed, so I deleted the Pod and created it again:
```bash
kubectl delete pod crashloop-pod
kubectl apply -f fixed.yaml
```
```text
pod "crashloop-pod" deleted from default namespace
pod/crashloop-pod created
```

## 5. Verify

```bash
kubectl get pod crashloop-pod
kubectl logs crashloop-pod
kubectl exec crashloop-pod -- printenv DATABASE_URL
```
```text
NAME            READY   STATUS    RESTARTS   AGE
crashloop-pod   1/1     Running   0          20s

Application started successfully! DB = postgres://db-service:5432/appdb

postgres://db-service:5432/appdb
```
What I observed: `1/1 Running`, `RESTARTS 0` after 20 seconds, and the app log says it started.

```bash
kubectl delete pod crashloop-pod
```

## Before / After

| | Before | After |
|---|---|---|
| STATUS | `Error` / `CrashLoopBackOff` | `Running` |
| RESTARTS | 3, 4, ... (growing) | 0 |
| Exit code | 1 | - (still running) |
| Log | `DATABASE_URL environment variable is MISSING!` | `Application started successfully!` |

## What I learned
- CrashLoopBackOff is almost always an **application** problem (bad config, missing env, wrong command, app bug). `describe` shows the exit code, `logs --previous` shows why.
- Other common causes: wrong `command`/`args`, a liveness probe killing the container, OOMKilled (exit code 137).
