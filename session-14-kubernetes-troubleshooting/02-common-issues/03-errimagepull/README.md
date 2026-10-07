# Issue 3 - ErrImagePull

**Problem statement:** A Pod (`errimagepull-pod`) was deployed with an image from our "company registry" and it fails right after creation.

**Files:** `broken.yaml`, `fixed.yaml`

## ErrImagePull vs ImagePullBackOff

```text
            first pull fails                 kubelet waits before retry
 Pulling  ------------------> ErrImagePull  ---------------------------> ImagePullBackOff
    ^                                                                          |
    +-------------------------------- retry ----------------------------------+
```
- **ErrImagePull** = the pull just failed (the actual error).
- **ImagePullBackOff** = kubelet is waiting before the next try.

They are two states of the same loop. You usually see `ErrImagePull` in the first seconds, then `ImagePullBackOff`. In Issue 2 the cause was a wrong tag; here I wanted a different cause - the registry itself can't be reached - and I caught the Pod in the `ErrImagePull` state.

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pod errimagepull-pod
```
```text
pod/errimagepull-pod created
NAME               READY   STATUS         RESTARTS   AGE
errimagepull-pod   0/1     ErrImagePull   0          2s
```

## 2. Investigate

```bash
kubectl describe pod errimagepull-pod
```
```text
    State:          Waiting
      Reason:       ErrImagePull
...
Events:
  Type     Reason     Age   From               Message
  ----     ------     ----  ----               -------
  Normal   Scheduled  2s    default-scheduler  Successfully assigned default/errimagepull-pod to minikube
  Normal   Pulling    1s    kubelet            Pulling image "registry.mycompany.invalid/nginx:1.27"
  Warning  Failed     1s    kubelet            Failed to pull image "registry.mycompany.invalid/nginx:1.27": failed to pull and unpack image "registry.mycompany.invalid/nginx:1.27": failed to resolve reference "registry.mycompany.invalid/nginx:1.27": failed to do request: Head "https://registry.mycompany.invalid/v2/nginx/manifests/1.27": dial tcp: lookup registry.mycompany.invalid on 192.168.65.254:53: no such host
  Warning  Failed     1s    kubelet            Error: ErrImagePull
  Normal   BackOff    1s    kubelet            Back-off pulling image "registry.mycompany.invalid/nginx:1.27"
  Warning  Failed     1s    kubelet            Error: ImagePullBackOff
```
What I observed: this time the error is not `not found` but **`lookup registry.mycompany.invalid ... no such host`** - the node could not even find the registry server. The events also show it moving to `ImagePullBackOff` right after.

Check the registry name from the node:
```bash
minikube ssh -- nslookup registry.mycompany.invalid
kubectl get pod errimagepull-pod -o jsonpath='{.spec.containers[0].image}'; echo
```
```text
Server:		192.168.65.254
Address:	192.168.65.254#53

** server can't find registry.mycompany.invalid: NXDOMAIN

ssh: Process exited with status 1

registry.mycompany.invalid/nginx:1.27
```

## 3. Root cause

The image points to a registry host `registry.mycompany.invalid` that does not exist (DNS `NXDOMAIN`). The image name and tag are fine - only the registry part is wrong. When no registry is written, Kubernetes uses Docker Hub (`docker.io/library/...`).

## 4. Fix

Use the correct (public) registry - I wrote the full name to make it clear:
```yaml
      image: docker.io/library/nginx:1.27
```
```bash
kubectl delete pod errimagepull-pod
kubectl apply -f fixed.yaml
```
```text
pod "errimagepull-pod" deleted from default namespace
pod/errimagepull-pod created
```

## 5. Verify

```bash
kubectl get pod errimagepull-pod
kubectl describe pod errimagepull-pod | sed -n '/^Events/,$p'
```
```text
NAME               READY   STATUS    RESTARTS   AGE
errimagepull-pod   1/1     Running   0          2s

Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  2s    default-scheduler  Successfully assigned default/errimagepull-pod to minikube
  Normal  Pulling    1s    kubelet            Pulling image "docker.io/library/nginx:1.27"
  Normal  Pulled     0s    kubelet            Successfully pulled image "docker.io/library/nginx:1.27" in 1.396s (1.396s including waiting). Image size: 68857691 bytes.
  Normal  Created    0s    kubelet            Container created
  Normal  Started    0s    kubelet            Container started
```

```bash
kubectl delete pod errimagepull-pod
```

## Before / After

| | Before | After |
|---|---|---|
| Image | `registry.mycompany.invalid/nginx:1.27` | `docker.io/library/nginx:1.27` |
| STATUS | `ErrImagePull` | `Running` |
| Event | `lookup registry.mycompany.invalid ... no such host` | `Successfully pulled image` |

## What I learned
- ErrImagePull and ImagePullBackOff are the same problem at different moments; always read the `Failed` event message for the real reason.
- `no such host` = registry name / DNS problem, `not found` = tag/name problem, `unauthorized` = need an `imagePullSecret`.
