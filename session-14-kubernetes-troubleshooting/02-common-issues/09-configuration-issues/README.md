# Issue 9 - Configuration issue (ConfigMap)

**Problem statement:** The `config-app` Deployment reads its settings from the ConfigMap `app-config`. After deploying, the rollout never finishes and the Pod does not start.

**Files:** `broken.yaml` (ConfigMap + Deployment), `fixed.yaml`

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pods -l app=config-app
kubectl rollout status deploy/config-app --timeout=10s
```
```text
configmap/app-config created
deployment.apps/config-app created
NAME                         READY   STATUS                       RESTARTS   AGE
config-app-6c4dcf9fb-xvwkk   0/1     CreateContainerConfigError   0          7s
Waiting for deployment "config-app" rollout to finish: 0 of 1 updated replicas are available...
error: timed out waiting for the condition
```
What I observed: status `CreateContainerConfigError` - kubelet could not build the container's configuration (env vars / volumes from ConfigMap or Secret).

## 2. Investigate

```bash
kubectl describe pod config-app-6c4dcf9fb-xvwkk
```
```text
    State:          Waiting
      Reason:       CreateContainerConfigError
    Environment:
      APP_MODE:   <set to the key 'APP_MODE' of config map 'app-config'>   Optional: false
      LOG_LEVEL:  <set to the key 'log_level' of config map 'app-config'>  Optional: false
...
Events:
  Type     Reason     Age               From               Message
  ----     ------     ----              ----               -------
  Normal   Scheduled  17s               default-scheduler  Successfully assigned default/config-app-6c4dcf9fb-xvwkk to minikube
  Normal   Pulled     4s (x3 over 17s)  kubelet            Container image "busybox:1.36" already present on machine and can be accessed by the pod
  Warning  Failed     4s (x3 over 17s)  kubelet            Error: couldn't find key APP_MODE in ConfigMap default/app-config
```

```bash
kubectl logs config-app-6c4dcf9fb-xvwkk
```
```text
Error from server (BadRequest): container "app" in pod "config-app-6c4dcf9fb-xvwkk" is waiting to start: CreateContainerConfigError
```
(no logs - the container never started)

Look at what the ConfigMap really contains:
```bash
kubectl get configmap app-config -o yaml | sed -n '/^data:/,/^kind/p'
```
```text
data:
  app_mode: production
  log_level: info
kind: ConfigMap
```

## 3. Root cause

The Deployment asks for key **`APP_MODE`** from the ConfigMap, but the ConfigMap key is **`app_mode`** (lower case). ConfigMap keys are case sensitive, so the key is "not found". Because the reference is not optional, kubelet refuses to create the container.

## 4. Fix

Make the `configMapKeyRef` key match the ConfigMap:
```yaml
            - name: APP_MODE
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: app_mode
```
```bash
kubectl apply -f fixed.yaml
kubectl rollout status deploy/config-app --timeout=90s
```
```text
configmap/app-config unchanged
deployment.apps/config-app configured
Waiting for deployment "config-app" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "config-app" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "config-app" rollout to finish: 1 old replicas are pending termination...
deployment "config-app" successfully rolled out
```

## 5. Verify

```bash
kubectl get pods -l app=config-app
kubectl logs deploy/config-app
kubectl exec deploy/config-app -- printenv APP_MODE LOG_LEVEL
```
```text
NAME                          READY   STATUS        RESTARTS   AGE
config-app-5d6f8b8c5b-mklw6   1/1     Running       0          0s
config-app-6c4dcf9fb-xvwkk    0/1     Terminating   0          18s

Found 2 pods, using pod/config-app-5d6f8b8c5b-mklw6
Starting in mode=production log=info

production
info
```
What I observed: the Deployment created a new ReplicaSet with the fixed template, the new Pod is Running and the old broken Pod is being removed. The app got both values.

```bash
kubectl delete -f fixed.yaml
```
```text
configmap "app-config" deleted from default namespace
deployment.apps "config-app" deleted from default namespace
```

## Before / After

| | Before | After |
|---|---|---|
| configMapKeyRef key | `APP_MODE` | `app_mode` |
| STATUS | `CreateContainerConfigError` | `Running` |
| Event / log | `couldn't find key APP_MODE in ConfigMap default/app-config` | `Starting in mode=production log=info` |

## What I learned
- `CreateContainerConfigError` = missing ConfigMap / Secret, or a missing key inside it. The event names the exact key.
- Other config mistakes I know of: wrong env value (app crashes -> CrashLoopBackOff, Issue 1), wrong mount path, ConfigMap in a different namespace.
- Changing a ConfigMap does **not** restart Pods that use it as env vars - you need `kubectl rollout restart`.
