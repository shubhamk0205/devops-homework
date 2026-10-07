# Issue 4 - Pending Pod

**Problem statement:** A Pod (`pending-pod`) was created but it stays `Pending` forever. It has no IP and no node.

**Files:** `broken.yaml`, `fixed.yaml`

`Pending` means the Pod was accepted by the API server but the **scheduler could not place it on any node** (or, less often, images are still downloading). Common reasons:

```text
 Pending
   |-- not enough CPU / memory on any node   <- this issue
   |-- nodeSelector / affinity matches no node
   |-- taints without matching tolerations
   |-- PVC not bound (waiting for storage)
   `-- too many pods on the node
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pod pending-pod -o wide
```
```text
pod/pending-pod created
NAME          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES
pending-pod   0/1     Pending   0          8s    <none>   <none>   <none>           <none>
```
What I observed: `NODE <none>` and `IP <none>` - the Pod was never scheduled.

## 2. Investigate

```bash
kubectl describe pod pending-pod
```
```text
    Requests:
      cpu:        500
      memory:     1000Gi
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  8s    default-scheduler  0/1 nodes are available: 1 Insufficient cpu, 1 Insufficient memory. preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
```
What I observed: the event comes from `default-scheduler` (not kubelet) and says **Insufficient cpu, Insufficient memory**. The Pod asks for 500 CPUs and 1000Gi RAM.

What does the node actually have?
```bash
kubectl get node minikube -o jsonpath='{.status.allocatable}'; echo
kubectl describe node minikube | sed -n '/Allocated resources/,/memory/p'
```
```text
{"cpu":"15","ephemeral-storage":"977850466304","hugepages-1Gi":"0","hugepages-2Mi":"0","hugepages-32Mi":"0","hugepages-64Ki":"0","memory":"20450800Ki","pods":"110"}

Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests    Limits
  --------           --------    ------
  cpu                1050m (7%)  100m (0%)
  memory             510Mi (2%)  220Mi (1%)
```
What I observed: the node can give at most 15 CPUs and ~19.5Gi memory. 500 CPUs / 1000Gi can never fit, so it would stay Pending forever.

## 3. Root cause

The resource **requests** are way bigger than any node in the cluster (`cpu: "500"`, `memory: "1000Gi"`). The scheduler only places a Pod on a node with enough free allocatable resources, so there is no valid node.

## 4. Fix

Request realistic values (and add limits):
```yaml
      resources:
        requests:
          cpu: 100m
          memory: 64Mi
        limits:
          cpu: 200m
          memory: 128Mi
```
Resource requests of a Pod can't be edited, so delete and re-create:
```bash
kubectl delete pod pending-pod
kubectl apply -f fixed.yaml
```
```text
pod "pending-pod" deleted from default namespace
pod/pending-pod created
```

## 5. Verify

```bash
kubectl get pod pending-pod -o wide
kubectl describe pod pending-pod | sed -n '/^Events/,$p'
```
```text
NAME          READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
pending-pod   1/1     Running   0          0s    10.244.0.84   minikube   <none>           <none>

Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  0s    default-scheduler  Successfully assigned default/pending-pod to minikube
  Normal  Pulled     0s    kubelet            Container image "nginx:1.27" already present on machine and can be accessed by the pod
  Normal  Created    0s    kubelet            Container created
  Normal  Started    0s    kubelet            Container started
```

```bash
kubectl delete pod pending-pod
```

## Before / After

| | Before | After |
|---|---|---|
| Requests | cpu 500, memory 1000Gi | cpu 100m, memory 64Mi |
| STATUS | `Pending`, NODE `<none>` | `Running` on `minikube` |
| Event | `FailedScheduling ... Insufficient cpu, Insufficient memory` | `Scheduled ... to minikube` |

## What I learned
- For Pending, look at the `FailedScheduling` event - it lists exactly why each node was rejected.
- Compare requests with `kubectl describe node` (Allocatable / Allocated resources).
- In a real cloud cluster the fix might also be adding nodes (cluster autoscaler) instead of lowering requests.
