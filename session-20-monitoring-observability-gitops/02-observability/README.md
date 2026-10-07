# Task 2: Observability - Metrics, Logs and Traces

In this task I wrote down what I understood about observability and its three pillars.
Where possible I link to what I actually saw in my monitoring demo ([Task 1](../01-monitoring/README.md)).

---

## 1. Monitoring vs Observability

```text
Monitoring    -> "Is something wrong?"        (known questions, dashboards + alerts)
Observability -> "WHY is it wrong?"           (ask new questions from the data the system gives out)
```

- **Monitoring** = watching known things: CPU > 80%? pod down? error rate high? You decide the checks in advance.
- **Observability** = how well you can understand the inside of a system just by looking at its outputs (metrics, logs, traces),
  even for a problem you never saw before.

Monitoring is a part of observability. Good observability makes monitoring useful.

Example from my demo: the `DemoAppReplicasUnavailable` alert (monitoring) told me "1 replica is missing".
To find out **why**, I needed more data: `kubectl describe` / events showed `Readiness probe failed ... statuscode: 403`,
and that pointed me to the missing `index.html`.

---

## 2. The three pillars

```text
              +-----------+       +-----------+       +------------+
              |  METRICS  |       |   LOGS    |       |   TRACES   |
              |  numbers  |       |  events   |       |  journey   |
              | over time |       | (text)    |       | of 1 req   |
              +-----+-----+       +-----+-----+       +------+-----+
                    |                   |                    |
            "how much / how      "what exactly         "where did the
              often?"              happened?"            time go?"
```

### Metrics

- **What:** numbers measured over time (time series) with labels. Small, cheap to store, fast to query.
- **Types:** counter (only goes up, e.g. `container_cpu_usage_seconds_total`), gauge (up and down, e.g. `container_memory_working_set_bytes`), histogram (buckets, e.g. request latency).
- **Good for:** dashboards, trends, alerts. E.g. CPU, memory, request rate, error rate, latency (p95/p99).
- **From my demo:** `rate(container_cpu_usage_seconds_total[1m])` showed my busy pod at ~0.5 cores; `kube_deployment_status_replicas_available` showed 2 -> 1 when a pod became not ready.
- **Limit:** a metric says *that* CPU is high, not *which* request or line of code caused it.

### Logs

- **What:** timestamped text records of events, written by apps and by the system.
- **Good for:** details and debugging: error messages, stack traces, who called what, status codes.
- **From my demo:** nginx access log line `"GET /notes HTTP/1.1" 404` and error log `open() "/usr/share/nginx/html/notes" failed (2: No such file or directory)`. Metrics never showed me this.
- **Tips:** structured logs (JSON) are easier to search; use log levels (INFO/WARN/ERROR); never log passwords.
- **Limit:** logs are big and expensive to store; in a distributed system logs are spread across many pods.

### Traces

- **What:** the path of **one request** through many services. A trace is made of **spans** (one span per step), all sharing a trace ID.

```text
Trace ID: 7f3a...   total 820 ms

frontend        |==|                                  20 ms
 order-service     |======|                           80 ms
  payment-service        |=========|                 120 ms
   database                        |==============|  600 ms   <-- slow part
```

- **Good for:** microservices, finding which service is slow or failing, seeing dependencies.
- **How:** the app is instrumented (e.g. OpenTelemetry SDK) and passes the trace ID in headers to the next service.
- **In my demo:** I did not set up tracing (only one nginx service, no instrumentation). For tracing you need something like OpenTelemetry + Jaeger/Tempo.

### How they work together

```text
  ALERT (metric)    : error rate of checkout > 5%                -> something is wrong
  TRACE             : slow/failed requests spend time in payment -> where it is wrong
  LOGS (payment pod): "ERROR db connection timeout"              -> why it is wrong
```

---

## 3. Why observability is required

- **Distributed systems are complex:** one user request can touch 10 microservices, pods move between nodes and restart. You cannot SSH in and "look".
- **Faster fixing (lower MTTR):** find the root cause in minutes instead of guessing.
- **Find problems before users do:** alerts on trends (memory growing, latency going up).
- **Capacity and cost:** real CPU/memory usage helps to set correct requests/limits and HPA (in my demo the busy pod used 813% of its CPU request).
- **Verify deployments:** after a new release, check errors/latency did not go up (useful with rollback in Helm / Argo CD).
- **SLOs:** you can only promise "99.9% available" if you measure it.

---

## 4. Common tools

| Pillar | Collect / store | View |
|---|---|---|
| Metrics | **Prometheus**, Thanos / Mimir (long-term), node-exporter, kube-state-metrics, cAdvisor | **Grafana** |
| Logs | **Loki** + Promtail/Alloy, ELK/EFK (Elasticsearch + Logstash/**Fluentd**/Fluent Bit + Kibana) | Grafana, Kibana |
| Traces | **OpenTelemetry** (instrumentation + collector), **Jaeger**, Grafana Tempo, Zipkin | Jaeger UI, Grafana |
| Alerts | Prometheus rules + **Alertmanager** (to Slack, email, PagerDuty) | |
| All-in-one (paid / SaaS) | Datadog, New Relic, Dynatrace, AWS CloudWatch, Google Cloud Operations, Azure Monitor | |

OpenTelemetry is the open standard to produce all three signals in one way, so you are not locked to one vendor.

---

## 5. Observability in Kubernetes

```text
   +------------------------------- Kubernetes cluster -------------------------------+
   |                                                                                  |
   |  Node:  kubelet + cAdvisor  ----> container CPU / memory metrics                 |
   |         node-exporter       ----> node CPU / memory / disk metrics               |
   |  API:   kube-state-metrics  ----> object state (replicas, ready, restarts)       |
   |  Pods:  app /metrics        ----> app metrics (requests, errors, latency)        |
   |         stdout / stderr     ----> logs  (/var/log/containers on the node)        |
   |         OpenTelemetry SDK   ----> traces                                         |
   |  Events (kubectl get events) ---> what Kubernetes did (scheduled, pulled, probe)  |
   +----------------------------------------------------------------------------------+
            |                        |                         |
        Prometheus               Loki / EFK              Jaeger / Tempo
            \________________________|_________________________/
                                  Grafana
```

Built-in things you get without installing anything:

| Command | What it shows |
|---|---|
| `kubectl top nodes / pods` | current CPU and memory (metrics-server) |
| `kubectl logs <pod>` / `-l app=x --prefix` / `--previous` | container logs (also of the crashed container) |
| `kubectl describe pod` | probe failures, restarts, OOMKilled, scheduling problems |
| `kubectl get events --sort-by=.lastTimestamp` | timeline of what happened in a namespace |
| readiness / liveness / startup probes | Kubernetes' own health checks for the app |

What we add on top (what I did in Task 1): the **kube-prometheus-stack** Helm chart = Prometheus Operator, Prometheus,
Alertmanager, Grafana, kube-state-metrics and node-exporter, with ready dashboards and alert rules.
The operator gives Kubernetes-style objects like `ServiceMonitor` (what to scrape) and `PrometheusRule` (alerts).

Kubernetes specific points:
- Pods are short-lived, so logs must be shipped out of the node (Loki/Fluent Bit), otherwise they disappear with the pod.
- Use **labels** (`app`, `namespace`, `pod`) to group metrics; `sum by (pod)` / `sum by (namespace)` in PromQL.
- Watch both levels: **cluster** (nodes, pods pending, restarts) and **application** (requests, errors, latency).

---

## What I learned

- Metrics = how much, logs = what happened, traces = where the time went. Each one alone is not enough.
- Monitoring tells you something is broken; observability lets you find out why.
- In Kubernetes a lot is available out of the box (`top`, `logs`, `events`, probes), and Prometheus + Grafana give history and alerts.
