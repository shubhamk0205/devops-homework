# Issue 5 - Stuck in ContainerCreating

**Problem statement:** A Pod (`containercreating-pod`) was scheduled on a node but stays in `ContainerCreating` and never starts.

**Files:** `broken.yaml`, `fixed.yaml`

`ContainerCreating` is normal for a few seconds (pulling image, setting up network, mounting volumes). If it stays there for long, something in that setup is failing. Most common: a **volume cannot be mounted** (missing Secret/ConfigMap, PVC problem) or the CNI network setup failed.

```text
 Pending --scheduled--> ContainerCreating --(mount volumes, network, pull image)--> Running
                                 ^
                          stuck here = a mount / network step is failing
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pod containercreating-pod
```
```text
pod/containercreating-pod created
NAME                    READY   STATUS              RESTARTS   AGE
containercreating-pod   0/1     ContainerCreating   0          22s
```
What I observed: nginx:1.27 was already on the node, so it should start in 1 second. 22 seconds in `ContainerCreating` is not normal.

## 2. Investigate

```bash
kubectl describe pod containercreating-pod
```
```text
    State:          Waiting
      Reason:       ContainerCreating
...
Volumes:
  db-secret:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  db-credentials
    Optional:    false
Events:
  Type     Reason       Age               From               Message
  ----     ------       ----              ----               -------
  Normal   Scheduled    22s               default-scheduler  Successfully assigned default/containercreating-pod to minikube
  Warning  FailedMount  6s (x6 over 22s)  kubelet            MountVolume.SetUp failed for volume "db-secret" : secret "db-credentials" not found
```
What I observed: scheduling worked, but kubelet keeps failing with `FailedMount ... secret "db-credentials" not found`. There is no `Pulled` event - kubelet does not even start the container until all volumes are mounted.

Does the Secret exist?
```bash
kubectl get secret db-credentials
kubectl get secrets
```
```text
Error from server (NotFound): secrets "db-credentials" not found
No resources found in default namespace.
```

## 3. Root cause

The Pod mounts a Secret volume named `db-credentials` (with `Optional: false`), but that Secret was never created in the `default` namespace. kubelet retries the mount forever and the container is never created. (`kubectl logs` would show nothing because there is no container yet.)

## 4. Fix

Create the missing Secret. The Pod spec was correct, so `fixed.yaml` is the Secret + the same Pod:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  username: appuser
  password: demo-only-not-a-real-password
```
```bash
kubectl apply -f fixed.yaml
```
```text
secret/db-credentials created
pod/containercreating-pod configured
```
I did not need to delete the Pod - kubelet retries the mount by itself.

## 5. Verify

```bash
kubectl get pod containercreating-pod
kubectl exec containercreating-pod -- ls /etc/db
kubectl describe pod containercreating-pod | sed -n '/^Events/,$p'
```
```text
NAME                    READY   STATUS    RESTARTS   AGE
containercreating-pod   1/1     Running   0          32s

password
username

Events:
  Type     Reason       Age                From               Message
  ----     ------       ----               ----               -------
  Normal   Scheduled    32s                default-scheduler  Successfully assigned default/containercreating-pod to minikube
  Warning  FailedMount  16s (x6 over 32s)  kubelet            MountVolume.SetUp failed for volume "db-secret" : secret "db-credentials" not found
  Normal   Pulled       0s                 kubelet            Container image "nginx:1.27" already present on machine and can be accessed by the pod
  Normal   Created      0s                 kubelet            Container created
  Normal   Started      0s                 kubelet            Container started
```
What I observed: as soon as the Secret existed, the next mount retry worked, and the container was created and started. The secret keys show up as files in `/etc/db`.

```bash
kubectl delete -f fixed.yaml
```
```text
secret "db-credentials" deleted from default namespace
pod "containercreating-pod" deleted from default namespace
```

## Before / After

| | Before | After |
|---|---|---|
| Secret `db-credentials` | not found | created |
| STATUS | `ContainerCreating` (stuck) | `Running` |
| Event | `FailedMount ... secret "db-credentials" not found` | `Container started` |

## What I learned
- Stuck `ContainerCreating` -> read the kubelet events: `FailedMount` (volume/secret/configmap/PVC) or `FailedCreatePodSandBox` (network/CNI).
- A Secret/ConfigMap must exist **in the same namespace** as the Pod.
- If a volume is truly optional, `optional: true` lets the Pod start without it.
