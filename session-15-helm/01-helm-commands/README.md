# Task 1: Helm Commands

In this task I practised all the important Helm commands from the session on my minikube cluster.
For every command I ran it, looked at what it does, and copied the real output here.

I used a separate namespace `helm-demo` for everything (`kubectl create namespace helm-demo`).

```text
Helm version : v4.3.0
Cluster      : minikube (Kubernetes v1.37)
Namespace    : helm-demo
Chart        : myapp/  (made with helm create)
```

## Quick idea of Helm

Helm is the package manager for Kubernetes. Instead of applying many YAML files one by one,
we package them as a **chart** (templates + values). When we install a chart, Helm creates a **release**.
Every install / upgrade / rollback makes a new **revision** of that release.

```text
   Chart (templates + values.yaml)
              |
        helm install / upgrade
              |
              v
   Release "myapp"  --->  revision 1, 2, 3 ...  (stored as Secrets in the namespace)
              |
              v
   Kubernetes objects (Deployment, Service, ServiceAccount ...)
```

## Command summary

| Command | What it does |
|---|---|
| `helm create` | Makes a new chart folder with starter templates |
| `helm install` | Installs a chart into the cluster and creates a release |
| `helm list` | Shows releases in a namespace |
| `helm status` | Shows the state of one release and its resources |
| `helm get` | Shows what was deployed (values, manifest, notes) for a release |
| `helm upgrade` | Changes a release (new values / new chart version), new revision |
| `helm history` | Shows all revisions of a release |
| `helm rollback` | Goes back to an older revision |
| `helm uninstall` | Deletes the release and all its Kubernetes objects |
| `helm repo` | Adds / lists / updates / removes chart repositories |
| `helm search` | Finds charts in added repos (`search repo`) or on Artifact Hub (`search hub`) |

---

## 1. helm create

```bash
helm create myapp
find myapp -type f | sort
```

```text
Creating myapp
myapp/.helmignore
myapp/Chart.yaml
myapp/templates/NOTES.txt
myapp/templates/_helpers.tpl
myapp/templates/deployment.yaml
myapp/templates/hpa.yaml
myapp/templates/httproute.yaml
myapp/templates/ingress.yaml
myapp/templates/service.yaml
myapp/templates/serviceaccount.yaml
myapp/templates/tests/test-connection.yaml
myapp/values.yaml
```

What I observed:
- `helm create` gives a full working chart for nginx. `Chart.yaml` has the chart metadata, `values.yaml` has default values, `templates/` has the Kubernetes YAML with `{{ }}` placeholders.
- By default the image tag is empty, so Helm uses `appVersion` (`1.16.0`) as the tag. That nginx tag is very old, so I changed one line in `values.yaml` to `tag: "1.25"`.

```bash
helm lint myapp
```

```text
==> Linting myapp
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

---

## 2. helm install

```bash
helm install myapp ./myapp -n helm-demo
```

```text
NAME: myapp
LAST DEPLOYED: Thu Oct  8 00:14:48 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace helm-demo -l "app.kubernetes.io/name=myapp,app.kubernetes.io/instance=myapp" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace helm-demo $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace helm-demo port-forward $POD_NAME 8080:$CONTAINER_PORT
```

```bash
kubectl get pods,svc -n helm-demo
```

```text
NAME                         READY   STATUS    RESTARTS   AGE
pod/myapp-55478c58d5-klqzd   1/1     Running   0          29s

NAME            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
service/myapp   ClusterIP   10.100.186.231   <none>        80/TCP    29s
```

What I observed:
- One command created the Deployment, Service and ServiceAccount. Release name is `myapp`, revision is 1.
- The `NOTES:` part comes from `templates/NOTES.txt`.

---

## 3. helm list

```bash
helm list -n helm-demo
```

```text
NAME 	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART      	APP VERSION
myapp	helm-demo	1       	2026-10-08 00:14:48.713635 +0530 IST	deployed	myapp-0.1.0	1.16.0
```

What I observed: shows every release in the namespace with its revision, status and chart version. (`helm list -A` shows all namespaces.)

---

## 4. helm status

```bash
helm status myapp -n helm-demo
```

```text
NAME: myapp
LAST DEPLOYED: Thu Oct  8 00:14:48 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
RESOURCES:
==> v1/Pod(related)
NAME                     READY   STATUS    RESTARTS   AGE
myapp-55478c58d5-klqzd   1/1     Running   0          29s

==> v1/ServiceAccount
NAME    AGE
myapp   29s

==> v1/Service
NAME    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
myapp   ClusterIP   10.100.186.231   <none>        80/TCP    29s

==> v1/Deployment
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
myapp   1/1     1            1           29s

NOTES:
...
```

What I observed: in Helm v4, `helm status` also lists the resources of the release, so I can see the pod and deployment health without running kubectl.

---

## 5. helm get

`helm get` has sub-commands: `values`, `manifest`, `notes`, `hooks`, `metadata`, `all`.

```bash
helm get values myapp -n helm-demo
helm get values myapp -n helm-demo --all | head -20
```

```text
USER-SUPPLIED VALUES:
null

COMPUTED VALUES:
affinity: {}
autoscaling:
  enabled: false
  maxReplicas: 100
  minReplicas: 1
  targetCPUUtilizationPercentage: 80
fullnameOverride: ""
httpRoute:
  annotations: {}
  enabled: false
...
```

```bash
helm get manifest myapp -n helm-demo | head -40
```

```text
---
# Source: myapp/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp
  labels:
    helm.sh/chart: myapp-0.1.0
    app.kubernetes.io/name: myapp
    app.kubernetes.io/instance: myapp
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
automountServiceAccountToken: true

---
# Source: myapp/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
...
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: http
      protocol: TCP
      name: http
...
```

```bash
helm get notes myapp -n helm-demo
```

```text
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace helm-demo -l "app.kubernetes.io/name=myapp,app.kubernetes.io/instance=myapp" -o jsonpath="{.items[0].metadata.name}")
  ...
```

What I observed:
- `get values` shows only what I passed with `--set`/`-f` (nothing yet, so `null`). With `--all` it shows the full merged values.
- `get manifest` shows the final YAML after the templates were rendered. This is what was really sent to Kubernetes.

---

## 6. helm upgrade

```bash
helm upgrade myapp ./myapp -n helm-demo --set replicaCount=2
```

```text
Release "myapp" has been upgraded. Happy Helming!
NAME: myapp
LAST DEPLOYED: Thu Oct  8 00:15:22 2026
NAMESPACE: helm-demo
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
...
```

```bash
kubectl get pods -n helm-demo
helm get values myapp -n helm-demo
```

```text
NAME                     READY   STATUS    RESTARTS   AGE
myapp-55478c58d5-klqzd   1/1     Running   0          35s
myapp-55478c58d5-knrj6   1/1     Running   0          1s

USER-SUPPLIED VALUES:
replicaCount: 2
```

What I observed: revision went from 1 to 2 and a second pod came up. Only the replica count changed, so the old pod stayed (same pod template hash).

---

## 7. helm history

```bash
helm history myapp -n helm-demo
```

```text
REVISION	UPDATED                 	STATUS    	CHART      	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:14:48 2026	superseded	myapp-0.1.0	1.16.0     	Install complete
2       	Thu Oct  8 00:15:22 2026	deployed  	myapp-0.1.0	1.16.0     	Upgrade complete
```

What I observed: the old revision is marked `superseded`, the current one is `deployed`.

---

## 8. helm rollback

```bash
helm rollback myapp 1 -n helm-demo
kubectl get pods -n helm-demo
helm history myapp -n helm-demo
```

```text
Rollback was a success! Happy Helming!

NAME                     READY   STATUS        RESTARTS   AGE
myapp-55478c58d5-klqzd   1/1     Running       0          35s
myapp-55478c58d5-knrj6   1/1     Terminating   0          1s

REVISION	UPDATED                 	STATUS    	CHART      	APP VERSION	DESCRIPTION
1       	Thu Oct  8 00:14:48 2026	superseded	myapp-0.1.0	1.16.0     	Install complete
2       	Thu Oct  8 00:15:22 2026	superseded	myapp-0.1.0	1.16.0     	Upgrade complete
3       	Thu Oct  8 00:15:23 2026	deployed  	myapp-0.1.0	1.16.0     	Rollback to 1
```

What I observed: rollback to revision 1 brought replicas back to 1 (the extra pod is terminating).
Rollback does not delete history, it creates a **new revision 3** which is a copy of revision 1.

---

## 9. helm uninstall

```bash
helm uninstall myapp -n helm-demo
helm list -n helm-demo
kubectl get all -n helm-demo
```

```text
release "myapp" uninstalled

NAME	NAMESPACE	REVISION	UPDATED	STATUS	CHART	APP VERSION

NAME                         READY   STATUS        RESTARTS   AGE
pod/myapp-55478c58d5-klqzd   1/1     Terminating   0          36s
pod/myapp-55478c58d5-knrj6   1/1     Terminating   0          2s
```

What I observed: the release is gone from `helm list` and all its objects are deleted (the pods were just finishing termination).

---

## 10. helm repo

```bash
helm repo list
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm repo list
```

```text
no repositories to show

"bitnami" has been added to your repositories

"prometheus-community" has been added to your repositories

Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
...Successfully got an update from the "bitnami" chart repository
Update Complete. ⎈Happy Helming!⎈

NAME                	URL
bitnami             	https://charts.bitnami.com/bitnami
prometheus-community	https://prometheus-community.github.io/helm-charts
```

```bash
helm repo remove bitnami
helm repo list
```

```text
"bitnami" has been removed from your repositories
NAME                	URL
prometheus-community	https://prometheus-community.github.io/helm-charts
```

What I observed: a repo is just a URL with an `index.yaml` of charts. `helm repo update` downloads the latest index (like `apt update`).
I kept `prometheus-community` because I need it in Session 20.

---

## 11. helm search

`helm search repo` searches the repos I added. `helm search hub` searches Artifact Hub (online).

```bash
helm search repo nginx | head -8
```

```text
NAME                                          	CHART VERSION	APP VERSION	DESCRIPTION
bitnami/nginx                                 	25.2.1       	1.31.6     	NGINX Open Source is a web server that can be a...
bitnami/nginx-ingress-controller              	12.0.7       	1.13.1     	NGINX Ingress Controller is an Ingress controll...
bitnami/nginx-intel                           	2.1.15       	0.4.9      	DEPRECATED NGINX Open Source for Intel is a lig...
prometheus-community/prometheus-nginx-exporter	1.23.1       	1.5.3      	A Helm chart for NGINX Prometheus Exporter
```

```bash
helm search repo prometheus-community/kube-prometheus-stack --versions | head -5
```

```text
NAME                                      	CHART VERSION	APP VERSION	DESCRIPTION
prometheus-community/kube-prometheus-stack	92.1.0       	v0.94.1    	kube-prometheus-stack collects Kubernetes manif...
prometheus-community/kube-prometheus-stack	92.0.0       	v0.94.1    	kube-prometheus-stack collects Kubernetes manif...
prometheus-community/kube-prometheus-stack	91.9.0       	v0.94.1    	kube-prometheus-stack collects Kubernetes manif...
prometheus-community/kube-prometheus-stack	91.8.2       	v0.94.1    	kube-prometheus-stack collects Kubernetes manif...
```

```bash
helm search hub nginx --max-col-width 60 | head -8
```

```text
URL                                                         	CHART VERSION  	APP VERSION	DESCRIPTION
https://artifacthub.io/packages/helm/cloudpirates-nginx/n...	0.16.12        	1.31.6     	Nginx is a high-performance HTTP server and reverse proxy.
https://artifacthub.io/packages/helm/quench-nginx/nginx     	0.0.15         	1.30.5     	High-performance web server, reverse proxy, and load bala...
https://artifacthub.io/packages/helm/krakazyabra/nginx      	1.0.0          	1.19.0     	Nginx Helm chart for Kubernetes
https://artifacthub.io/packages/helm/dhinesh/nginx          	25.2.1         	1.31.6     	NGINX Open Source is a web server that can be also used a...
https://artifacthub.io/packages/helm/bitnami/nginx          	25.2.1         	1.31.6     	NGINX Open Source is a web server that can be also used a...
...
```

What I observed:
- `CHART VERSION` is the version of the chart package, `APP VERSION` is the version of the app inside it. They are different numbers.
- `--versions` lists all older chart versions too, useful when you want to pin one.
- `helm search hub` returns many community charts, so it is better to pick official/verified ones.

---

## What I learned

- Helm turns many YAML files into one package that can be installed with one command and configured with values.
- Every change is a revision, and `helm history` + `helm rollback` make going back very easy.
- `helm get manifest` / `helm template` are the best way to check what Helm really sends to the cluster.
- Using `-n <namespace>` on every command is important, because releases are stored per namespace.
