# Task 1 - Kubernetes Troubleshooting Commands

In this task I practiced the main kubectl commands used for troubleshooting. I deployed a small nginx app (`web-deployment.yaml` - Deployment `web` with 2 replicas + Service `web-service`) and a Pod that prints logs (`logs-demo-pod.yaml`), then ran each command against them on minikube.

```bash
kubectl apply -f web-deployment.yaml -f logs-demo-pod.yaml
```
```text
deployment.apps/web created
service/web-service created
pod/logs-demo created
```

Where each command fits when something is broken:

```text
 kubectl get        -> WHAT is the status?            (Running? Pending? CrashLoopBackOff?)
 kubectl describe   -> WHY? details + Events          (scheduling, image pull, probes, mounts)
 kubectl events     -> WHAT HAPPENED in order?        (all events of namespace / one object)
 kubectl logs       -> what did the APP say?          (stack traces, errors)
 kubectl exec       -> go INSIDE and test             (curl, nslookup, env, files)
 kubectl top        -> is it out of CPU / memory?
 kubectl explain    -> what does this YAML field mean?
 kubectl get -o wide-> which NODE / IP?
```

---

## 1. kubectl get

Shows a short status table of resources.

```bash
kubectl get pods
```
```text
NAME                   READY   STATUS    RESTARTS   AGE
logs-demo              1/1     Running   0          0s
web-7f98c7b879-csnbt   1/1     Running   0          0s
web-7f98c7b879-xrlt5   1/1     Running   0          0s
```

Many resource types at once:
```bash
kubectl get deploy,rs,svc
```
```text
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   2/2     2            2           1s

NAME                             DESIRED   CURRENT   READY   AGE
replicaset.apps/web-7f98c7b879   2         2         2       0s

NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/kubernetes    ClusterIP   10.96.0.1      <none>        443/TCP   38m
service/web-service   ClusterIP   10.97.48.221   <none>        80/TCP    0s
```

Labels (very useful for Service selector problems) and filtering by label:
```bash
kubectl get pods --show-labels
kubectl get pods -l app=web
```
```text
NAME                   READY   STATUS    RESTARTS   AGE   LABELS
logs-demo              1/1     Running   0          0s    app=logs-demo
web-7f98c7b879-csnbt   1/1     Running   0          0s    app=web,pod-template-hash=7f98c7b879
web-7f98c7b879-xrlt5   1/1     Running   0          0s    app=web,pod-template-hash=7f98c7b879

NAME                   READY   STATUS    RESTARTS   AGE
web-7f98c7b879-csnbt   1/1     Running   0          0s
web-7f98c7b879-xrlt5   1/1     Running   0          0s
```

All namespaces:
```bash
kubectl get pods -A | head -12
```
```text
NAMESPACE       NAME                                       READY   STATUS      RESTARTS      AGE
default         logs-demo                                  1/1     Running     0             0s
default         web-7f98c7b879-csnbt                       1/1     Running     0             0s
default         web-7f98c7b879-xrlt5                       1/1     Running     0             0s
ingress-nginx   ingress-nginx-admission-create-nxkjl       0/1     Completed   0             38m
ingress-nginx   ingress-nginx-admission-patch-zwcdk        0/1     Completed   2 (38m ago)   38m
ingress-nginx   ingress-nginx-controller-d7cd8c989-6bx28   1/1     Running     0             38m
kube-system     coredns-559f6c778d-fx6c5                   1/1     Running     0             38m
kube-system     etcd-minikube                              1/1     Running     0             38m
kube-system     kindnet-s4xcb                              1/1     Running     0             38m
kube-system     kube-apiserver-minikube                    1/1     Running     0             38m
kube-system     kube-controller-manager-minikube           1/1     Running     0             38m
```

Full YAML of the live object, and custom output with jsonpath:
```bash
kubectl get pod logs-demo -o yaml | head -25
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\t"}{.status.podIP}{"\n"}{end}'
```
```text
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      ...
  creationTimestamp: "2026-10-07T19:20:01Z"
  generation: 1
  labels:
    app: logs-demo
  name: logs-demo
  namespace: default
  ...

logs-demo	Running	10.244.0.76
web-7f98c7b879-csnbt	Running	10.244.0.77
web-7f98c7b879-xrlt5	Running	10.244.0.75
```

What I observed: `get` is always the first command. It answers "is it running and ready?". `-o yaml` shows the full live spec + status, which is handy to compare with my YAML file.

---

## 2. kubectl get -o wide

Same table with extra columns: Pod IP, node, and for Services the selector.

```bash
kubectl get pods -o wide
```
```text
NAME                   READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
logs-demo              1/1     Running   0          1s    10.244.0.76   minikube   <none>           <none>
web-7f98c7b879-csnbt   1/1     Running   0          1s    10.244.0.77   minikube   <none>           <none>
web-7f98c7b879-xrlt5   1/1     Running   0          1s    10.244.0.75   minikube   <none>           <none>
```

```bash
kubectl get nodes -o wide
```
```text
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION             CONTAINER-RUNTIME
minikube   Ready    control-plane   38m   v1.37.0   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.12.76-linuxkit (arm64)   containerd://2.3.4
```

```bash
kubectl get svc -o wide
```
```text
NAME          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
kubernetes    ClusterIP   10.96.0.1      <none>        443/TCP   38m   <none>
web-service   ClusterIP   10.97.48.221   <none>        80/TCP    1s    app=web
```

What I observed: `-o wide` tells me which node a Pod is on (important when one node is broken) and the Pod IPs, which I can compare with Service endpoints. For a Service it shows the `SELECTOR` directly.

---

## 3. kubectl describe

Shows everything about one object in a readable form, and the **Events** at the bottom. Most problems (scheduling, image pull, probes, mounts) are explained in these events.

```bash
kubectl describe pod web-7f98c7b879-csnbt
```
```text
Name:             web-7f98c7b879-csnbt
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Thu, 08 Oct 2026 00:50:01 +0530
Labels:           app=web
                  pod-template-hash=7f98c7b879
Status:           Running
IP:               10.244.0.77
Controlled By:  ReplicaSet/web-7f98c7b879
Containers:
  nginx:
    Container ID:   containerd://75e4cc98aa3bdc2772f33ad790b2eb6a952d15cb98022576a619a719dc4561a4
    Image:          nginx:1.27
    Port:           80/TCP
    State:          Running
      Started:      Thu, 08 Oct 2026 00:50:01 +0530
    Ready:          True
    Restart Count:  0
    Requests:
      cpu:        50m
      memory:     32Mi
...
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
...
QoS Class:                   Burstable
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  7s    default-scheduler  Successfully assigned default/web-7f98c7b879-csnbt to minikube
  Normal  Pulled     7s    kubelet            Container image "nginx:1.27" already present on machine and can be accessed by the pod
  Normal  Created    7s    kubelet            Container created
  Normal  Started    7s    kubelet            Container started
```

```bash
kubectl describe service web-service
```
```text
Name:                     web-service
Namespace:                default
Selector:                 app=web
Type:                     ClusterIP
IP:                       10.97.48.221
Port:                     <unset>  80/TCP
TargetPort:               80/TCP
Endpoints:                10.244.0.75:80,10.244.0.77:80
Session Affinity:         None
Internal Traffic Policy:  Cluster
Events:                   <none>
```

```bash
kubectl describe deployment web | head -30
```
```text
Name:                   web
Namespace:              default
Selector:               app=web
Replicas:               2 desired | 2 updated | 2 total | 2 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  25% max unavailable, 25% max surge
...
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
```

Node capacity (useful for `Pending` Pods):
```bash
kubectl describe node minikube | sed -n '/Allocated resources/,/Events/p'
```
```text
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests    Limits
  --------           --------    ------
  cpu                1150m (7%)  100m (0%)
  memory             574Mi (2%)  220Mi (1%)
  ephemeral-storage  0 (0%)      0 (0%)
...
```

What I observed: in the Service describe, `Endpoints` = the 2 Pod IPs from `get pods -o wide`, so the Service is connected to the Pods. In Pod describe the most useful parts are `State`, `Restart Count`, `Conditions` and `Events`.

---

## 4. kubectl logs

Shows what the container printed to stdout/stderr.

```bash
kubectl logs logs-demo
```
```text
Application started
Connecting to database...
Database connection successful
Application is running
Wed Oct  7 19:20:01 UTC 2026 Application is healthy
Wed Oct  7 19:20:06 UTC 2026 Application is healthy
```

Last N lines / with timestamps:
```bash
kubectl logs logs-demo --tail=2
kubectl logs logs-demo --since=10s --timestamps
```
```text
Wed Oct  7 19:20:01 UTC 2026 Application is healthy
Wed Oct  7 19:20:06 UTC 2026 Application is healthy

2026-10-07T19:20:01.607728794Z Application started
2026-10-07T19:20:01.607751294Z Connecting to database...
2026-10-07T19:20:01.607755377Z Database connection successful
2026-10-07T19:20:01.607756169Z Application is running
2026-10-07T19:20:01.609600169Z Wed Oct  7 19:20:01 UTC 2026 Application is healthy
2026-10-07T19:20:06.613422088Z Wed Oct  7 19:20:06 UTC 2026 Application is healthy
```

Follow live (like `tail -f`, stopped with Ctrl+C):
```bash
kubectl logs -f logs-demo --tail=1
```
```text
Wed Oct  7 19:22:31 UTC 2026 Application is healthy
Wed Oct  7 19:22:36 UTC 2026 Application is healthy
Wed Oct  7 19:22:41 UTC 2026 Application is healthy
```

Logs of all Pods with a label, and of a Deployment + specific container (`-c`):
```bash
kubectl logs -l app=web --prefix --tail=3
kubectl logs deploy/web -c nginx --tail=3
```
```text
[pod/web-7f98c7b879-csnbt/nginx] 2026/10/07 19:20:01 [notice] 1#1: start worker process 41
[pod/web-7f98c7b879-csnbt/nginx] 2026/10/07 19:20:01 [notice] 1#1: start worker process 42
[pod/web-7f98c7b879-csnbt/nginx] 2026/10/07 19:20:01 [notice] 1#1: start worker process 43
[pod/web-7f98c7b879-xrlt5/nginx] 2026/10/07 19:20:01 [notice] 1#1: start worker process 41
[pod/web-7f98c7b879-xrlt5/nginx] 2026/10/07 19:20:01 [notice] 1#1: start worker process 42
[pod/web-7f98c7b879-xrlt5/nginx] 2026/10/07 19:20:01 [notice] 1#1: start worker process 43

Found 2 pods, using pod/web-7f98c7b879-csnbt
2026/10/07 19:20:01 [notice] 1#1: start worker process 41
2026/10/07 19:20:01 [notice] 1#1: start worker process 42
2026/10/07 19:20:01 [notice] 1#1: start worker process 43
```

What I observed: `logs` shows the application's view of the problem. For a crashing container, `kubectl logs <pod> --previous` shows logs from the last crashed run (I used it in the CrashLoopBackOff task).

---

## 5. kubectl exec

Runs a command inside a running container - for testing from the Pod's point of view.

```bash
kubectl exec web-7f98c7b879-csnbt -- curl -s -o /dev/null -w 'HTTP %{http_code}\n' localhost
```
```text
HTTP 200
```

DNS config and environment variables inside the Pod:
```bash
kubectl exec web-7f98c7b879-csnbt -- cat /etc/resolv.conf
kubectl exec web-7f98c7b879-csnbt -- env | grep -E 'HOSTNAME|WEB_SERVICE'
```
```text
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5

HOSTNAME=web-7f98c7b879-csnbt
WEB_SERVICE_PORT_80_TCP=tcp://10.97.48.221:80
WEB_SERVICE_PORT_80_TCP_PROTO=tcp
WEB_SERVICE_PORT_80_TCP_ADDR=10.97.48.221
WEB_SERVICE_SERVICE_HOST=10.97.48.221
WEB_SERVICE_SERVICE_PORT=80
WEB_SERVICE_PORT=tcp://10.97.48.221:80
WEB_SERVICE_PORT_80_TCP_PORT=80
```

Files and an interactive-style shell (normally `kubectl exec -it <pod> -- sh`; here I piped the commands in with `-i`):
```bash
kubectl exec web-7f98c7b879-csnbt -- ls /usr/share/nginx/html
printf 'hostname\nnginx -v\nexit\n' | kubectl exec -i web-7f98c7b879-csnbt -- sh
```
```text
50x.html
index.html

web-7f98c7b879-csnbt
nginx version: nginx/1.27.5
```

Test Service + DNS from another Pod:
```bash
kubectl exec logs-demo -- wget -qO- http://web-service | head -4
kubectl exec logs-demo -- nslookup web-service.default.svc.cluster.local
```
```text
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>

Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	web-service.default.svc.cluster.local
Address: 10.97.48.221
```

What I observed: the Pod uses CoreDNS at `10.96.0.10`, and `web-service` resolves to the Service ClusterIP `10.97.48.221`. `exec` is the only way to test "can Pod A reach Service B" from inside the cluster.

---

## 6. kubectl events

Events are short messages that Kubernetes components (scheduler, kubelet, controllers) write about objects. `kubectl events` is the newer command; `kubectl get events` also works.

```bash
kubectl events | tail -15
```
```text
2m53s               Normal    Scheduled                      Pod/web-7f98c7b879-csnbt               Successfully assigned default/web-7f98c7b879-csnbt to minikube
2m53s               Normal    Started                        Pod/web-7f98c7b879-csnbt               Container started
2m53s               Normal    Created                        Pod/logs-demo                          Container created
2m53s               Normal    Pulled                         Pod/logs-demo                          Container image "busybox:1.36" already present on machine and can be accessed by the pod
...
2m53s               Normal    SuccessfulCreate               ReplicaSet/web-7f98c7b879              Created pod: web-7f98c7b879-xrlt5
2m53s               Normal    SuccessfulCreate               ReplicaSet/web-7f98c7b879              Created pod: web-7f98c7b879-csnbt
2m53s               Normal    ScalingReplicaSet              Deployment/web                         Scaled up replica set web-7f98c7b879 from 0 to 2
```

Only events for one object:
```bash
kubectl events --for pod/web-7f98c7b879-csnbt
```
```text
LAST SEEN   TYPE     REASON      OBJECT                     MESSAGE
2m53s       Normal   Scheduled   Pod/web-7f98c7b879-csnbt   Successfully assigned default/web-7f98c7b879-csnbt to minikube
2m53s       Normal   Pulled      Pod/web-7f98c7b879-csnbt   Container image "nginx:1.27" already present on machine and can be accessed by the pod
2m53s       Normal   Created     Pod/web-7f98c7b879-csnbt   Container created
2m53s       Normal   Started     Pod/web-7f98c7b879-csnbt   Container started
```

Old style, sorted by time:
```bash
kubectl get events --sort-by=.lastTimestamp | tail -6
```
```text
2m53s       Normal    Pulled                         pod/web-7f98c7b879-xrlt5               Container image "nginx:1.27" already present on machine and can be accessed by the pod
2m53s       Normal    Created                        pod/web-7f98c7b879-xrlt5               Container created
2m53s       Normal    Started                        pod/web-7f98c7b879-xrlt5               Container started
2m53s       Normal    SuccessfulCreate               replicaset/web-7f98c7b879              Created pod: web-7f98c7b879-xrlt5
2m53s       Normal    SuccessfulCreate               replicaset/web-7f98c7b879              Created pod: web-7f98c7b879-csnbt
2m53s       Normal    ScalingReplicaSet              deployment/web                         Scaled up replica set web-7f98c7b879 from 0 to 2
```

Only warnings, in all namespaces:
```bash
kubectl events --types=Warning -A | head -8
```
```text
NAMESPACE       LAST SEEN           TYPE      REASON                         OBJECT                                         MESSAGE
kube-system     41m (x2 over 41m)   Warning   Unhealthy                      Pod/kube-scheduler-minikube                    Readiness probe failed: HTTP probe failed with statuscode: 500
kube-system     41m                 Warning   FailedScheduling               Pod/storage-provisioner                        0/1 nodes are available: 1 node(s) had untolerated taint(s). preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
kube-system     41m                 Warning   NodeNotReady                   Pod/kube-scheduler-minikube                    Node is not ready
ingress-nginx   41m                 Warning   FailedScheduling               Pod/ingress-nginx-admission-create-nxkjl       0/1 nodes are available: 1 node(s) had untolerated taint(s). preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
...
```

What I observed: the warning events show what happened while minikube was booting - system Pods could not be scheduled for a few seconds because the node still had the "not-ready" taint. They fixed themselves once the node was Ready. Events are kept only for about 1 hour by default.

---

## 7. kubectl explain

Built-in documentation for every YAML field. Very helpful when I'm not sure about a field name or allowed values.

```bash
kubectl explain pod.spec.containers.imagePullPolicy
```
```text
KIND:       Pod
VERSION:    v1

FIELD: imagePullPolicy <string>
ENUM:
    Always
    IfNotPresent
    Never

DESCRIPTION:
    Image pull policy. One of Always, Never, IfNotPresent. Defaults to Always if
    :latest tag is specified, or IfNotPresent otherwise. Cannot be updated. More
    info: https://kubernetes.io/docs/concepts/containers/images#updating-images
...
```

```bash
kubectl explain deployment.spec.strategy
```
```text
GROUP:      apps
KIND:       Deployment
VERSION:    v1

FIELD: strategy <DeploymentStrategy>

DESCRIPTION:
    The deployment strategy to use to replace existing pods with new ones.
    DeploymentStrategy describes how to replace existing pods with new ones.
    
FIELDS:
  rollingUpdate	<RollingUpdateDeployment>
    Rolling update config params. Present only if DeploymentStrategyType =
    RollingUpdate.

  type	<string>
  enum: Recreate, RollingUpdate
    Type of deployment. Can be "Recreate" or "RollingUpdate". Default is
    RollingUpdate.
...
```

```bash
kubectl explain service.spec.selector
kubectl explain pod.spec.containers.resources --recursive | head -20
```
```text
KIND:       Service
VERSION:    v1

FIELD: selector <map[string]string>

DESCRIPTION:
    Route service traffic to pods with label keys and values matching this
    selector. If empty or not present, the service is assumed to have an
    external process managing its endpoints, which Kubernetes will not modify.
...

KIND:       Pod
VERSION:    v1

FIELD: resources <ResourceRequirements>
...
FIELDS:
  claims	<[]ResourceClaim>
    name	<string> -required-
    request	<string>
  limits	<map[string]Quantity>
  requests	<map[string]Quantity>
```

What I observed: `--recursive` shows the whole tree of sub-fields, so I can check the right spelling and nesting without opening the docs website.

---

## 8. kubectl top

Shows real CPU and memory usage (needs metrics-server).

```bash
kubectl top nodes
kubectl top pods
```
```text
NAME       CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)   
minikube   156m         1%       2595Mi          12%         

NAME                   CPU(cores)   MEMORY(bytes)   
logs-demo              1m           0Mi             
web-7f98c7b879-csnbt   0m           11Mi            
web-7f98c7b879-xrlt5   0m           11Mi            
```

```bash
kubectl top pods -A --sort-by=memory | head -6
kubectl top pod logs-demo --containers
```
```text
NAMESPACE       NAME                                       CPU(cores)   MEMORY(bytes)   
kube-system     kube-apiserver-minikube                    39m          957Mi           
ingress-nginx   ingress-nginx-controller-d7cd8c989-6bx28   6m           182Mi           
kube-system     etcd-minikube                              19m          140Mi           
kube-system     kube-controller-manager-minikube           13m          96Mi            
kube-system     kube-scheduler-minikube                    7m           34Mi            

POD         NAME   CPU(cores)   MEMORY(bytes)   
logs-demo   app    1m           0Mi             
```

What I observed: `--sort-by=memory` quickly shows the heaviest Pods (here the API server). `top` helps when a Pod is slow or gets OOMKilled.

---

## Cleanup

```bash
kubectl delete -f web-deployment.yaml -f logs-demo-pod.yaml
```
```text
deployment.apps "web" deleted from default namespace
service "web-service" deleted from default namespace
pod "logs-demo" deleted from default namespace
```

## Quick reference

| Command | Use it for |
|---------|-----------|
| `kubectl get pods` / `-o wide` / `--show-labels` / `-o yaml` | status, IP, node, labels, full spec |
| `kubectl describe pod/svc/deploy/node <name>` | details + Events (the "why") |
| `kubectl logs <pod>` / `-f` / `--previous` / `-c` / `-l` | app output, last crash, multi container |
| `kubectl exec <pod> -- <cmd>` / `-it ... -- sh` | test from inside (curl, nslookup, env, cat files) |
| `kubectl events` / `--for` / `--types=Warning` | timeline of what happened |
| `kubectl explain <path>` / `--recursive` | meaning of a YAML field |
| `kubectl top nodes/pods` | real CPU / memory usage |
