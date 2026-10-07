# Issue 2 - ImagePullBackOff

**Problem statement:** A new nginx Pod (`imagepull-pod`) never starts. It stays `0/1` and no container is created.

**Files:** `broken.yaml`, `fixed.yaml`

`ImagePullBackOff` means kubelet tried to pull the image, it failed (`ErrImagePull`), and now kubelet is **waiting** before trying again. Like CrashLoopBackOff, the wait gets longer each time (up to 5 minutes).

```text
 Pulling -> ErrImagePull -> ImagePullBackOff (wait) -> Pulling -> ErrImagePull -> ImagePullBackOff (longer wait) ...
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pod imagepull-pod
```
```text
pod/imagepull-pod created
NAME            READY   STATUS             RESTARTS   AGE
imagepull-pod   0/1     ImagePullBackOff   0          49s
```
What I observed: `RESTARTS 0` - the container was never even created, so this is not an app crash. The status itself points to the image.

## 2. Investigate

```bash
kubectl describe pod imagepull-pod
```
```text
Containers:
  web:
    Container ID:   
    Image:          nginx:1.277
    Image ID:       
    ...
    State:          Waiting
      Reason:       ImagePullBackOff
    Ready:          False
    Restart Count:  0
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Normal   Scheduled  49s                default-scheduler  Successfully assigned default/imagepull-pod to minikube
  Normal   BackOff    16s (x2 over 46s)  kubelet            Back-off pulling image "nginx:1.277"
  Warning  Failed     16s (x2 over 46s)  kubelet            Error: ImagePullBackOff
  Normal   Pulling    5s (x3 over 48s)   kubelet            Pulling image "nginx:1.277"
  Warning  Failed     3s (x3 over 47s)   kubelet            Failed to pull image "nginx:1.277": rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/library/nginx:1.277": failed to resolve reference "docker.io/library/nginx:1.277": docker.io/library/nginx:1.277: not found
  Warning  Failed     3s (x3 over 47s)   kubelet            Error: ErrImagePull
```

Same thing with `kubectl events`:
```bash
kubectl events --for pod/imagepull-pod
```
```text
LAST SEEN           TYPE      REASON      OBJECT              MESSAGE
49s                 Normal    Scheduled   Pod/imagepull-pod   Successfully assigned default/imagepull-pod to minikube
16s (x2 over 46s)   Normal    BackOff     Pod/imagepull-pod   Back-off pulling image "nginx:1.277"
16s (x2 over 46s)   Warning   Failed      Pod/imagepull-pod   Error: ImagePullBackOff
5s (x3 over 48s)    Normal    Pulling     Pod/imagepull-pod   Pulling image "nginx:1.277"
3s (x3 over 47s)    Warning   Failed      Pod/imagepull-pod   Failed to pull image "nginx:1.277": rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/library/nginx:1.277": failed to resolve reference "docker.io/library/nginx:1.277": docker.io/library/nginx:1.277: not found
3s (x3 over 47s)    Warning   Failed      Pod/imagepull-pod   Error: ErrImagePull
```

To be sure it's the tag and not a network problem, I tried pulling both tags directly on the node:
```bash
minikube ssh -- sudo crictl pull nginx:1.277
minikube ssh -- sudo crictl pull nginx:1.27
```
```text
... FATA[0001] pulling image: rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/library/nginx:1.277": failed to resolve reference "docker.io/library/nginx:1.277": docker.io/library/nginx:1.277: not found 
ssh: Process exited with status 1

Image is up to date for sha256:7791402a0bf5691936db0f42d40032ac6fb8441867416053f3ea06199de3e7e4
```
What I observed: the registry (Docker Hub) was reachable - it answered `NotFound`. `nginx:1.27` works, `nginx:1.277` does not exist.

## 3. Root cause

Typo in the image tag: `nginx:1.277` instead of `nginx:1.27`. Docker Hub has no such tag, so every pull returns `not found`.

## 4. Fix

```yaml
      image: nginx:1.27
```
The image of a Pod can be changed in place, but to keep it clean I recreated it:
```bash
kubectl delete pod imagepull-pod
kubectl apply -f fixed.yaml
```
```text
pod "imagepull-pod" deleted from default namespace
pod/imagepull-pod created
```

## 5. Verify

```bash
kubectl get pod imagepull-pod
kubectl describe pod imagepull-pod | sed -n '/^Events/,$p'
```
```text
NAME            READY   STATUS    RESTARTS   AGE
imagepull-pod   1/1     Running   0          1s

Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  1s    default-scheduler  Successfully assigned default/imagepull-pod to minikube
  Normal  Pulled     0s    kubelet            Container image "nginx:1.27" already present on machine and can be accessed by the pod
  Normal  Created    0s    kubelet            Container created
  Normal  Started    0s    kubelet            Container started
```

```bash
kubectl delete pod imagepull-pod
```

## Before / After

| | Before | After |
|---|---|---|
| Image | `nginx:1.277` | `nginx:1.27` |
| STATUS | `ImagePullBackOff` | `Running` |
| Event | `docker.io/library/nginx:1.277: not found` | `Container started` |

## What I learned
- Common causes of ImagePullBackOff: wrong tag, wrong image name, private image without `imagePullSecrets`, registry rate limit, no internet on the node.
- The **message** in the `Failed` event tells which one: `not found` = name/tag wrong, `pull access denied` / `unauthorized` = credentials, `no such host` / `i/o timeout` = network/DNS (see Issue 3).
