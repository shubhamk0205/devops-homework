# Task 2: Helm Rollback Workflow

In this task I did a full rollback workflow on one release:

```text
Install (nginx 1.25, 1 replica)          -> revision 1
   |
Upgrade (nginx 1.27, 2 replicas)         -> revision 2
   |
Verify  (image 1.27, 2/2 ready)          OK
   |
Upgrade again (bad image tag)            -> revision 3  (FAILED)
   |
Verify  (ErrImagePull)                   BROKEN
   |
Rollback to revision 2                   -> revision 4
   |
Verify  (image 1.27, 2/2 ready)          OK again
```

I reused the chart from Task 1 (`../01-helm-commands/myapp`) and released it as `web` in the `helm-demo` namespace.
Because the chart name is `myapp` and the release is `web`, the Deployment is called `web-myapp`.

---

## Step 1: Install

```bash
helm install web ./01-helm-commands/myapp -n helm-demo --set image.tag=1.25 --wait --timeout 3m
```

```text
NAME: web
LAST DEPLOYED: Thu Oct  8 00:16:24 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
...
```

```bash
kubectl get deploy web-myapp -n helm-demo -o wide
kubectl exec -n helm-demo deploy/web-myapp -- nginx -v
```

```text
NAME        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
web-myapp   1/1     1            1           1s    myapp        nginx:1.25   app.kubernetes.io/instance=web,app.kubernetes.io/name=myapp

nginx version: nginx/1.25.5
```

What I observed: `--wait` makes Helm wait until the pods are ready before it says `deployed`.

---

## Step 2: Upgrade (good change)

```bash
helm upgrade web ./01-helm-commands/myapp -n helm-demo --set image.tag=1.27 --set replicaCount=2 --wait --timeout 3m
```

```text
Release "web" has been upgraded. Happy Helming!
NAME: web
LAST DEPLOYED: Thu Oct  8 00:16:25 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
...
```

## Step 3: Verify

```bash
kubectl get deploy web-myapp -n helm-demo -o wide
kubectl exec -n helm-demo deploy/web-myapp -- nginx -v
helm get values web -n helm-demo
helm history web -n helm-demo
```

```text
NAME        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
web-myapp   2/2     2            2           3s    myapp        nginx:1.27   app.kubernetes.io/instance=web,app.kubernetes.io/name=myapp

nginx version: nginx/1.27.5

USER-SUPPLIED VALUES:
image:
  tag: "1.27"
replicaCount: 2

REVISION	UPDATED                 	STATUS    	CHART      	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:16:24 2026	superseded	myapp-0.1.0	1.16.0     	Install complete
2       	Thu Oct  8 00:16:25 2026	deployed  	myapp-0.1.0	1.16.0     	Upgrade complete
```

What I observed: 2 pods running nginx 1.27. This is the "good" version I want to go back to later.

---

## Step 4: Upgrade again (bad change)

Here I made a mistake on purpose: an image tag that does not exist.

```bash
helm upgrade web ./01-helm-commands/myapp -n helm-demo --set image.tag=9.99-does-not-exist --set replicaCount=2 --wait --timeout 60s
```

```text
level=WARN msg="upgrade failed" name=web error="resource Deployment/helm-demo/web-myapp not ready. status: InProgress, message: Updated: 1/2\ncontext deadline exceeded"
Error: UPGRADE FAILED: resource Deployment/helm-demo/web-myapp not ready. status: InProgress, message: Updated: 1/2
context deadline exceeded
```

## Step 5: Verify (it is broken)

```bash
kubectl get deploy web-myapp -n helm-demo -o wide
kubectl get pods -n helm-demo
helm history web -n helm-demo
```

```text
NAME        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                      SELECTOR
web-myapp   2/2     1            2           71s   myapp        nginx:9.99-does-not-exist   app.kubernetes.io/instance=web,app.kubernetes.io/name=myapp

NAME                         READY   STATUS         RESTARTS   AGE
web-myapp-6765fffd56-6hb8f   1/1     Running        0          69s
web-myapp-6765fffd56-w4lg2   1/1     Running        0          69s
web-myapp-7fcd7d7fb9-kxkm2   0/1     ErrImagePull   0          60s

REVISION	UPDATED                 	STATUS    	CHART      	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:16:24 2026	superseded	myapp-0.1.0	1.16.0     	Install complete
2       	Thu Oct  8 00:16:25 2026	deployed  	myapp-0.1.0	1.16.0     	Upgrade complete
3       	Thu Oct  8 00:16:35 2026	failed    	myapp-0.1.0	1.16.0     	Upgrade "web" failed: resource Deployment/helm-demo/web-myapp not ready. status: InProgress, message: Updated: ...
```

What I observed:
- The new pod is stuck in `ErrImagePull`. The 2 old pods are still running because of the rolling update strategy, so users were not fully down.
- Because I used `--wait`, Helm noticed the pods never became ready and marked revision 3 as `failed`.

---

## Step 6: Rollback

```bash
helm rollback web 2 -n helm-demo --wait --timeout 3m
```

```text
Rollback was a success! Happy Helming!
```

## Step 7: Verify (healthy again)

```bash
kubectl rollout status deploy/web-myapp -n helm-demo
kubectl get deploy web-myapp -n helm-demo -o wide
kubectl get pods -n helm-demo
kubectl exec -n helm-demo deploy/web-myapp -- nginx -v
helm history web -n helm-demo
helm get values web -n helm-demo
```

```text
deployment "web-myapp" successfully rolled out

NAME        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
web-myapp   2/2     2            2           71s   myapp        nginx:1.27   app.kubernetes.io/instance=web,app.kubernetes.io/name=myapp

NAME                         READY   STATUS        RESTARTS   AGE
web-myapp-6765fffd56-6hb8f   1/1     Running       0          69s
web-myapp-6765fffd56-w4lg2   1/1     Running       0          69s
web-myapp-7fcd7d7fb9-kxkm2   0/1     Terminating   0          60s

nginx version: nginx/1.27.5

REVISION	UPDATED                 	STATUS    	CHART      	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:16:24 2026	superseded	myapp-0.1.0	1.16.0     	Install complete
2       	Thu Oct  8 00:16:25 2026	superseded	myapp-0.1.0	1.16.0     	Upgrade complete
3       	Thu Oct  8 00:16:35 2026	failed    	myapp-0.1.0	1.16.0     	Upgrade "web" failed: resource Deployment/helm-demo/web-myapp not ready. status: InProgress, message: Updated: ...
4       	Thu Oct  8 00:17:35 2026	deployed  	myapp-0.1.0	1.16.0     	Rollback to 2

USER-SUPPLIED VALUES:
image:
  tag: "1.27"
replicaCount: 2
```

What I observed:
- The broken pod is terminated, image is back to `nginx:1.27` with 2/2 ready.
- Rollback made a new revision 4 ("Rollback to 2"). The failed revision 3 stays in history, so I can still see what went wrong.

---

## Clean up

```bash
helm uninstall web -n helm-demo
```

```text
release "web" uninstalled
```

## What I learned

- Always check `helm history` first to find the last good revision number before rolling back.
- `--wait --timeout` is useful in upgrades: Helm marks the release `failed` instead of saying `deployed` for a broken app.
- Rollback is fast because Helm already stores every revision; it just re-applies the old manifest.
- Rolling update kept the old pods alive during the bad upgrade, so Kubernetes and Helm together reduce downtime.
