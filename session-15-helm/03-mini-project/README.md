# Task 3: Mini Project - Notes App with Helm

In this mini project I packaged the "Notes" app as a Helm chart (`notes-chart`) and deployed it,
upgraded it to production values, broke it with a bad upgrade and rolled it back.
The app is a simple nginx pod that represents the Notes web app (same as in the session).

Namespace used: `helm-demo`.

## Chart structure

```text
notes-chart/
  Chart.yaml           -> chart name, chart version 0.1.0, appVersion 1.0
  values.yaml          -> dev values  (1 replica, nginx 1.24, environment=development)
  values-prod.yaml     -> prod values (3 replicas, nginx 1.25, environment=production)
  templates/
    configmap.yaml     -> APP_NAME and ENVIRONMENT from values
    deployment.yaml    -> replicas + image from values, env loaded from the ConfigMap
    service.yaml       -> NodePort 30090
```

```text
  values.yaml / values-prod.yaml
           |
           v
  templates/*.yaml  --(helm renders {{ .Values.x }} / {{ .Release.Name }})-->  real YAML
           |
           v
  ConfigMap notes-dev-config  -->  Deployment notes-dev-deploy  <--  Service notes-dev-svc (NodePort 30090)
```

### values.yaml vs values-prod.yaml

| Key | values.yaml (dev) | values-prod.yaml |
|---|---|---|
| replicaCount | 1 | 3 |
| image.tag | 1.24 | 1.25 |
| app.environment | development | production |

### Templates

`templates/deployment.yaml` (main parts):

```yaml
metadata:
  name: {{ .Release.Name }}-deploy
spec:
  replicas: {{ .Values.replicaCount }}
  ...
        - name: notes
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
```

`templates/configmap.yaml`:

```yaml
data:
  APP_NAME: {{ .Values.app.name | quote }}
  ENVIRONMENT: {{ .Values.app.environment | quote }}
```

`.Release.Name` makes every object name unique per release, so the same chart can be installed many times.

---

## Step 1: Lint

```bash
helm lint notes-chart
helm lint notes-chart -f notes-chart/values-prod.yaml
```

```text
==> Linting notes-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

==> Linting notes-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

## Step 2: Render locally

```bash
helm template notes-dev notes-chart
```

```text
---
# Source: notes-chart/templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: notes-dev-config
data:
  APP_NAME: "notes-app"
  ENVIRONMENT: "development"

---
# Source: notes-chart/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: notes-dev-svc
spec:
  type: NodePort
  selector:
    app: notes-dev
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30090

---
# Source: notes-chart/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notes-dev-deploy
  labels:
    app: notes-dev
    environment: development
spec:
  replicas: 1
  ...
        - name: notes
          image: "nginx:1.24"
          ...
          envFrom:
            - configMapRef:
                name: notes-dev-config
```

What I observed: all `{{ }}` were replaced. This is a safe way to check the YAML before touching the cluster.

---

## Step 3: Install (development)

```bash
helm install notes-dev notes-chart -n helm-demo
```

```text
NAME: notes-dev
LAST DEPLOYED: Thu Oct  8 00:17:46 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

```bash
kubectl get pods,svc,configmap -n helm-demo
kubectl exec -n helm-demo deploy/notes-dev-deploy -- printenv APP_NAME ENVIRONMENT
kubectl get deploy notes-dev-deploy -n helm-demo -o wide
```

```text
NAME                                    READY   STATUS    RESTARTS   AGE
pod/notes-dev-deploy-74956bd987-fbq6k   1/1     Running   0          20s

NAME                    TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/notes-dev-svc   NodePort   10.105.239.249   <none>        80:30090/TCP   20s

NAME                         DATA   AGE
configmap/kube-root-ca.crt   1      3m27s
configmap/notes-dev-config   2      20s

notes-app
development

NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
notes-dev-deploy   1/1     1            1           20s   notes        nginx:1.24   app=notes-dev
```

What I observed: the ConfigMap values reached the container as environment variables (`APP_NAME`, `ENVIRONMENT`).

I opened the app in the browser with a port-forward (on Mac with the docker driver, NodePort is not directly reachable, so port-forward is easier):

```bash
kubectl port-forward -n helm-demo svc/notes-dev-svc 18090:80
```

![Notes app (dev release) in browser](../screenshots/notes-dev-v1.png)

---

## Step 4: Upgrade to production values

```bash
helm upgrade notes-dev notes-chart -n helm-demo -f notes-chart/values-prod.yaml
```

```text
Release "notes-dev" has been upgraded. Happy Helming!
NAME: notes-dev
LAST DEPLOYED: Thu Oct  8 00:18:26 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

```bash
kubectl rollout status deploy/notes-dev-deploy -n helm-demo --timeout=120s
kubectl get deploy notes-dev-deploy -n helm-demo -o wide
kubectl get configmap notes-dev-config -n helm-demo -o jsonpath='{.data}'
helm history notes-dev -n helm-demo
```

```text
Waiting for deployment "notes-dev-deploy" rollout to finish: 1 out of 3 new replicas have been updated...
...
Waiting for deployment "notes-dev-deploy" rollout to finish: 1 old replicas are pending termination...
deployment "notes-dev-deploy" successfully rolled out

NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
notes-dev-deploy   3/3     3            3           42s   notes        nginx:1.25   app=notes-dev

{"APP_NAME":"notes-app","ENVIRONMENT":"production"}

REVISION	UPDATED                 	STATUS    	CHART            	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:17:46 2026	superseded	notes-chart-0.1.0	1.0        	Install complete
2       	Thu Oct  8 00:18:26 2026	deployed  	notes-chart-0.1.0	1.0        	Upgrade complete
```

What I observed: 3 replicas, image 1.25 and ENVIRONMENT=production. Only the values file changed, not the templates.

---

## Step 5: Simulate a bad upgrade

```bash
helm upgrade notes-dev notes-chart -n helm-demo -f notes-chart/values-prod.yaml --set image.tag=broken-tag-does-not-exist
sleep 25
kubectl get pods -n helm-demo
helm history notes-dev -n helm-demo
```

```text
Release "notes-dev" has been upgraded. Happy Helming!
NAME: notes-dev
LAST DEPLOYED: Thu Oct  8 00:18:28 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
TEST SUITE: None

NAME                                READY   STATUS             RESTARTS   AGE
notes-dev-deploy-79b4dbdffd-px9cd   0/1     ImagePullBackOff   0          25s
notes-dev-deploy-bbcc464b4-62mgl    1/1     Running            0          27s
notes-dev-deploy-bbcc464b4-dctld    1/1     Running            0          26s
notes-dev-deploy-bbcc464b4-fqllw    1/1     Running            0          26s

REVISION	UPDATED                 	STATUS    	CHART            	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:17:46 2026	superseded	notes-chart-0.1.0	1.0        	Install complete
2       	Thu Oct  8 00:18:26 2026	superseded	notes-chart-0.1.0	1.0        	Upgrade complete
3       	Thu Oct  8 00:18:28 2026	deployed  	notes-chart-0.1.0	1.0        	Upgrade complete
```

What I observed: without `--wait`, Helm says `deployed` even though the new pod is in `ImagePullBackOff`.
Helm only checks that Kubernetes accepted the YAML. So we must always verify the pods ourselves (or use `--wait`, like in Task 2).

---

## Step 6: Rollback to revision 2

```bash
helm rollback notes-dev 2 -n helm-demo
kubectl rollout status deploy/notes-dev-deploy -n helm-demo --timeout=120s
kubectl get pods -n helm-demo
kubectl get deploy notes-dev-deploy -n helm-demo -o wide
helm history notes-dev -n helm-demo
helm list -n helm-demo
```

```text
Rollback was a success! Happy Helming!

deployment "notes-dev-deploy" successfully rolled out

NAME                               READY   STATUS    RESTARTS   AGE
notes-dev-deploy-bbcc464b4-62mgl   1/1     Running   0          32s
notes-dev-deploy-bbcc464b4-dctld   1/1     Running   0          31s
notes-dev-deploy-bbcc464b4-fqllw   1/1     Running   0          31s

NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
notes-dev-deploy   3/3     3            3           72s   notes        nginx:1.25   app=notes-dev

REVISION	UPDATED                 	STATUS    	CHART            	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:17:46 2026	superseded	notes-chart-0.1.0	1.0        	Install complete
2       	Thu Oct  8 00:18:26 2026	superseded	notes-chart-0.1.0	1.0        	Upgrade complete
3       	Thu Oct  8 00:18:28 2026	superseded	notes-chart-0.1.0	1.0        	Upgrade complete
4       	Thu Oct  8 00:18:53 2026	deployed  	notes-chart-0.1.0	1.0        	Rollback to 2

NAME     	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART            	APP VERSION
notes-dev	helm-demo	4       	2026-10-08 00:18:53.557488 +0530 IST	deployed	notes-chart-0.1.0	1.0
```

Checked the app is serving again with the right nginx version:

```bash
kubectl port-forward -n helm-demo svc/notes-dev-svc 18090:80 &
curl -sI http://localhost:18090 | head -3
```

```text
HTTP/1.1 200 OK
Server: nginx/1.25.5
Date: Wed, 07 Oct 2026 18:49:07 GMT
```

What I observed: the broken pod is gone, 3 healthy pods with nginx 1.25 (the prod revision). History shows the rollback as revision 4.

---

## Step 7: Clean up

```bash
helm uninstall notes-dev -n helm-demo
kubectl get pods,svc,configmap -n helm-demo
helm list -n helm-demo
kubectl delete namespace helm-demo
```

```text
release "notes-dev" uninstalled

NAME                         DATA   AGE
configmap/kube-root-ca.crt   1      4m38s

NAME	NAMESPACE	REVISION	UPDATED	STATUS	CHART	APP VERSION

namespace "helm-demo" deleted
```

What I observed: Deployment, Service and our ConfigMap are all gone (`kube-root-ca.crt` is created by Kubernetes in every namespace, not by Helm).

---

## What I practised

```text
[PASS] Created a Helm chart (Chart.yaml, values.yaml, values-prod.yaml, templates)
[PASS] Checked it with helm lint and helm template
[PASS] Installed the dev release
[PASS] Upgraded to production values (1 -> 3 replicas, nginx 1.24 -> 1.25)
[PASS] Simulated a bad upgrade (ImagePullBackOff)
[PASS] Rolled back to the healthy revision 2
[PASS] Cleaned up with helm uninstall
```

## What I learned

- One chart + different values files = different environments (dev / prod) without copying YAML.
- `helm upgrade` without `--wait` does not tell you the app is broken, you need to check pods.
- `helm rollback <release> <revision>` is the quickest way to recover from a bad release.
