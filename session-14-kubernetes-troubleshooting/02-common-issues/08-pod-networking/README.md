# Issue 8 - Pod networking issue

**Problem statement:** `net-client` needs to call a small Python API running in `api-pod` on port 8000 using the Pod IP. Both Pods are `Running`, but the call fails with "Connection refused".

**Files:** `broken.yaml` (api-pod + net-client), `fixed.yaml`

In Kubernetes every Pod gets its own IP and every Pod can reach every other Pod IP directly (flat network, provided by the CNI plugin - kindnet in minikube). So when Pod-to-Pod fails, I check layer by layer:

```text
 net-client 10.244.0.96  ---- network (CNI) ---->  api-pod 10.244.0.95
                                                       |
   1. is the Pod IP reachable at all?  (ping)          |  2. is the app listening?
                                                       |  3. on WHICH address? 127.0.0.1 or 0.0.0.0
```

## 1. Identify the problem

```bash
kubectl apply -f broken.yaml
kubectl get pods -o wide
kubectl exec net-client -- wget -q -T 3 -O- http://10.244.0.95:8000
```
```text
pod/api-pod created
pod/net-client created
NAME         READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
api-pod      1/1     Running   0          2s    10.244.0.95   minikube   <none>           <none>
net-client   1/1     Running   0          2s    10.244.0.96   minikube   <none>           <none>
wget: can't connect to remote host (10.244.0.95): Connection refused
command terminated with exit code 1
```

## 2. Investigate

Step 1 - is the network between the Pods OK?
```bash
kubectl exec net-client -- ping -c 2 10.244.0.95
```
```text
PING 10.244.0.95 (10.244.0.95): 56 data bytes
64 bytes from 10.244.0.95: seq=0 ttl=63 time=0.913 ms
64 bytes from 10.244.0.95: seq=1 ttl=63 time=0.181 ms

--- 10.244.0.95 ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.181/0.547/0.913 ms
```
What I observed: ping works, so the CNI/Pod network is fine. "Connection refused" (not a timeout) also means the packet reached the Pod but nothing accepted it on that port.

Step 2 - does the app work from inside its own Pod?
```bash
kubectl exec api-pod -- wget -q -T 3 -O- http://127.0.0.1:8000 | head -3
kubectl logs api-pod
```
```text
<!DOCTYPE HTML>
<html lang="en">
<head>

Serving HTTP on 127.0.0.1 port 8000 (http://127.0.0.1:8000/) ...
127.0.0.1 - - [07/Oct/2026 19:36:09] "GET / HTTP/1.1" 200 -
```
What I observed: from inside the Pod it works. The log line says `Serving HTTP on 127.0.0.1`.

Step 3 - which address is the server listening on?
```bash
kubectl exec api-pod -- netstat -tln
kubectl get pod api-pod -o jsonpath='{.spec.containers[0].command}'; echo
```
```text
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       
tcp        0      0 127.0.0.1:8000          0.0.0.0:*               LISTEN      

["python3","-m","http.server","8000","--bind","127.0.0.1"]
```

## 3. Root cause

The server is started with `--bind 127.0.0.1`, so it listens only on the **loopback** interface inside the Pod. Connections that come to the Pod IP `10.244.0.95` (eth0) are refused. The Kubernetes network was fine - the app was not listening on the Pod's network interface.

## 4. Fix

Bind to all interfaces:
```yaml
      command: ["python3", "-m", "http.server", "8000", "--bind", "0.0.0.0"]
```
```bash
kubectl delete pod api-pod
kubectl apply -f fixed.yaml
```
```text
pod "api-pod" deleted from default namespace
pod/api-pod created
pod/net-client unchanged
```

## 5. Verify

(The new Pod got a new IP: 10.244.0.97.)
```bash
kubectl get pod api-pod -o wide
kubectl exec api-pod -- netstat -tln
kubectl exec net-client -- wget -q -T 3 -O- http://10.244.0.97:8000 | head -3
kubectl logs api-pod
```
```text
NAME      READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
api-pod   1/1     Running   0          2s    10.244.0.97   minikube   <none>           <none>

Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       
tcp        0      0 0.0.0.0:8000            0.0.0.0:*               LISTEN      

<!DOCTYPE HTML>
<html lang="en">
<head>

Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
10.244.0.96 - - [07/Oct/2026 19:36:42] "GET / HTTP/1.1" 200 -
```
What I observed: now it listens on `0.0.0.0:8000`, and the access log shows the request came from `10.244.0.96` = the net-client Pod.

Note: the first time I ran this scenario, the verify step also failed with "Connection refused", because I ran wget the same second the Pod became Running and Python had not opened the port yet (there is no readiness probe). Also `kubectl logs` was empty because Python buffered its output. So I added `PYTHONUNBUFFERED=1` to both YAMLs, ran the whole scenario again, and waited until `netstat` showed the port before testing - the output above is from that second run. A readiness probe would avoid the timing problem in a real app.

```bash
kubectl delete -f fixed.yaml
```
```text
pod "api-pod" deleted from default namespace
pod "net-client" deleted from default namespace
```

## Before / After

| | Before | After |
|---|---|---|
| bind address | `127.0.0.1` | `0.0.0.0` |
| netstat | `127.0.0.1:8000 LISTEN` | `0.0.0.0:8000 LISTEN` |
| from net-client | `Connection refused` | HTTP 200 |

## What I learned
- `ping` works + `Connection refused` = network OK, app/port problem. `ping` fails or **timeout** = network problem (CNI, NetworkPolicy, node network).
- Apps in containers must listen on `0.0.0.0`, not `localhost`. This is a very common mistake with dev servers (Flask, Node, Python http.server).
- Pod IPs change on every re-create - that's why we normally use a Service instead of Pod IPs.
