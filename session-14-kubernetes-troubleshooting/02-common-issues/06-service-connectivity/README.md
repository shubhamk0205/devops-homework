# Issue 6 - Service connectivity issue

**Problem statement:** The `shop` Pods are `Running`, but other Pods cannot reach the app through `shop-service` - they get "Connection refused".

**Files:** `broken.yaml` (Deployment + Service + test client Pod), `fixed.yaml`

How a request reaches the app, and what can break at each step:

```text
 client Pod --> shop-service:80 (ClusterIP) --> Endpoints (PodIP:targetPort) --> nginx in Pod listening on containerPort
                    |                               |                                  |
              wrong name/port?            selector matches labels?           targetPort == port app listens on?
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pods -l app=shop -o wide; kubectl get pod client
kubectl exec client -- wget -q -T 3 -O- http://shop-service
```
```text
deployment.apps/shop created
service/shop-service created
pod/client created
NAME                    READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
shop-74b8fb5545-4ztv2   1/1     Running   0          0s    10.244.0.86   minikube   <none>           <none>
shop-74b8fb5545-nhln5   1/1     Running   0          0s    10.244.0.88   minikube   <none>           <none>
NAME     READY   STATUS    RESTARTS   AGE
client   1/1     Running   0          0s
wget: can't connect to remote host (10.107.239.203): Connection refused
command terminated with exit code 1
```
What I observed: Pods are healthy, DNS works (`shop-service` was resolved to `10.107.239.203`), but the connection is refused.

## 2. Investigate

```bash
kubectl get svc shop-service
kubectl describe svc shop-service
```
```text
NAME           TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
shop-service   ClusterIP   10.107.239.203   <none>        80/TCP    2s

Name:                     shop-service
Namespace:                default
Selector:                 app=shop
Type:                     ClusterIP
IP:                       10.107.239.203
Port:                     <unset>  80/TCP
TargetPort:               8080/TCP
Endpoints:                10.244.0.86:8080,10.244.0.88:8080
...
```

```bash
kubectl get endpointslices -l kubernetes.io/service-name=shop-service
```
```text
NAME                 ADDRESSTYPE   PORTS   ENDPOINTS                 AGE
shop-service-9652r   IPv4          8080    10.244.0.86,10.244.0.88   2s
```
What I observed: the selector is fine - the Endpoints are exactly the 2 shop Pod IPs. But traffic is sent to port **8080** on those Pods.

Test the Pod directly on both ports, and check which port the container really uses:
```bash
kubectl exec client -- wget -q -T 3 -O- http://10.244.0.86:8080
kubectl exec client -- wget -q -T 3 -O- http://10.244.0.86:80 | head -4
kubectl get deploy shop -o jsonpath='{.spec.template.spec.containers[0].ports}'; echo
```
```text
wget: can't connect to remote host (10.244.0.86): Connection refused
command terminated with exit code 1

<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>

[{"containerPort":80,"protocol":"TCP"}]
```
What I observed: Pod port 8080 refuses, Pod port 80 answers. So the Pods are fine and the Service points to the wrong port.

## 3. Root cause

The Service has `targetPort: 8080`, but nginx listens on port **80** (`containerPort: 80`). The Service forwards to a port where nothing is listening, so the connection is refused.

## 4. Fix

```yaml
  ports:
    - port: 80
      targetPort: 80
```
```bash
kubectl apply -f fixed.yaml
```
```text
deployment.apps/shop unchanged
service/shop-service configured
pod/client unchanged
```

## 5. Verify

```bash
kubectl describe svc shop-service | grep -E 'TargetPort|Endpoints'
kubectl exec client -- wget -q -T 3 -O- http://shop-service | head -4
```
```text
TargetPort:               80/TCP
Endpoints:                10.244.0.88:80,10.244.0.86:80

<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
```

```bash
kubectl delete -f fixed.yaml
```
```text
deployment.apps "shop" deleted from default namespace
service "shop-service" deleted from default namespace
pod "client" deleted from default namespace
```

## Before / After

| | Before | After |
|---|---|---|
| targetPort | 8080 | 80 |
| Endpoints | `10.244.0.86:8080,10.244.0.88:8080` | `10.244.0.88:80,10.244.0.86:80` |
| `wget http://shop-service` | `Connection refused` | nginx welcome page |

## What I learned
Service checklist:
1. `kubectl get endpoints/endpointslices` - **empty** = selector does not match Pod labels (or Pods not Ready). I do that case in the mini project.
2. Endpoints present but `refused` = **targetPort** wrong (this issue).
3. Test the Pod IP directly to split "Pod problem" from "Service problem".
