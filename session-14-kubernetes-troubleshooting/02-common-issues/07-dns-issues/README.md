# Issue 7 - DNS issue

**Problem statement:** The `orders-client` Pod calls the `orders-api` backend every 5 seconds, but every call fails. The backend Pod is running fine.

**Files:** `broken.yaml` (backend Deployment + Service + client Pod), `fixed.yaml`

How Service DNS works in Kubernetes:

```text
 orders-client Pod
    | wget http://<name>
    | /etc/resolv.conf -> nameserver 10.96.0.10 (CoreDNS), search default.svc.cluster.local ...
    v
 CoreDNS  -- knows every Service:  <service>.<namespace>.svc.cluster.local -> ClusterIP
    |
    v
 orders-api Service 10.106.98.43 -> orders-api Pod
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pods
kubectl logs orders-client --tail=3
```
```text
deployment.apps/orders-api created
service/orders-api created
pod/orders-client created
NAME                          READY   STATUS    RESTARTS   AGE
orders-api-68fdc85f77-nf79g   1/1     Running   0          16s
orders-client                 1/1     Running   0          16s

19:33:16 FAIL - cannot reach http://orders-svc
wget: bad address 'orders-svc'
19:33:21 FAIL - cannot reach http://orders-svc
```
What I observed: everything is `Running`, but the client log says `bad address 'orders-svc'`. "bad address" from busybox wget = the hostname could not be resolved.

## 2. Investigate

Reproduce from inside the client and do a DNS lookup:
```bash
kubectl exec orders-client -- wget -q -T 3 -O /dev/null http://orders-svc
kubectl exec orders-client -- nslookup orders-svc.default.svc.cluster.local
```
```text
wget: bad address 'orders-svc'
command terminated with exit code 1

Server:		10.96.0.10
Address:	10.96.0.10:53

** server can't find orders-svc.default.svc.cluster.local: NXDOMAIN

** server can't find orders-svc.default.svc.cluster.local: NXDOMAIN

command terminated with exit code 1
```

Is DNS itself working? Check resolv.conf, CoreDNS and a name that surely exists:
```bash
kubectl exec orders-client -- cat /etc/resolv.conf
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl exec orders-client -- nslookup kubernetes.default.svc.cluster.local
```
```text
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5

NAME                       READY   STATUS    RESTARTS   AGE
coredns-559f6c778d-fx6c5   1/1     Running   0          52m

Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	kubernetes.default.svc.cluster.local
Address: 10.96.0.1
```
What I observed: CoreDNS is running and resolves `kubernetes.default` fine. So DNS works - the **name** `orders-svc` simply does not exist (NXDOMAIN).

What Services do exist?
```bash
kubectl get svc
kubectl exec orders-client -- nslookup orders-api.default.svc.cluster.local
```
```text
NAME         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.96.0.1      <none>        443/TCP   52m
orders-api   ClusterIP   10.106.98.43   <none>        80/TCP    16s

Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	orders-api.default.svc.cluster.local
Address: 10.106.98.43
```

## 3. Root cause

The client is configured with `ORDERS_URL=http://orders-svc`, but the Service is named **`orders-api`**. There is no DNS record for `orders-svc`, so CoreDNS answers NXDOMAIN and wget fails with "bad address". DNS and the backend were both healthy - it was a wrong hostname in the app config.

## 4. Fix

Use the correct Service name. I used the full name so it also works from other namespaces:
```yaml
      env:
        - name: ORDERS_URL
          value: "http://orders-api.default.svc.cluster.local"
```
```bash
kubectl delete pod orders-client
kubectl apply -f fixed.yaml
```
```text
pod "orders-client" deleted from default namespace
deployment.apps/orders-api unchanged
service/orders-api unchanged
pod/orders-client created
```

## 5. Verify

```bash
kubectl get pods
kubectl logs orders-client --tail=3
```
```text
NAME                          READY   STATUS    RESTARTS   AGE
orders-api-68fdc85f77-nf79g   1/1     Running   0          59s
orders-client                 1/1     Running   0          12s

19:33:53 OK   - reached http://orders-api.default.svc.cluster.local
19:33:58 OK   - reached http://orders-api.default.svc.cluster.local
19:34:03 OK   - reached http://orders-api.default.svc.cluster.local
```

```bash
kubectl delete -f fixed.yaml
```
```text
deployment.apps "orders-api" deleted from default namespace
service "orders-api" deleted from default namespace
pod "orders-client" deleted from default namespace
```

## Before / After

| | Before | After |
|---|---|---|
| ORDERS_URL | `http://orders-svc` | `http://orders-api.default.svc.cluster.local` |
| nslookup | `NXDOMAIN` | `10.106.98.43` |
| client log | `FAIL - cannot reach` | `OK - reached` |

## What I learned
- DNS name format: `<service>.<namespace>.svc.cluster.local`. Inside the same namespace just `<service>` works because of the `search` line in resolv.conf.
- To debug DNS: first test a name that must work (`kubernetes.default`). If that fails -> CoreDNS/network problem. If only your name fails -> wrong name or wrong namespace.
