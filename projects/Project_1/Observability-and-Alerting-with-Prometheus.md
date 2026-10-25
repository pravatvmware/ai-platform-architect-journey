---
title: "Observability and Alerting with Prometheus"
parent: "3. Project 1"
nav_order: 3
---

# Prometheus: Monitoring and Observation in Microservices

**Prometheus** is an open-source, metrics-based monitoring and alerting toolkit designed specifically for dynamic, cloud-native environments like microservices. Unlike traditional monitoring systems that wait for services to push logs or status updates, Prometheus actively pulls numeric data from your services, making it highly effective for distributed systems.

---

## 🏛️ How Prometheus Works in Microservices

In a microservices architecture, dozens or hundreds of small services run independently. Prometheus observes this environment using a **pull-based architecture** and a few core components:

* **Service Discovery:** Microservices are dynamic; they constantly scale up, down, or relocate. Prometheus automatically discovers these changes by integrating with platforms like Kubernetes, Consul, or AWS EC2 to find the exact IP addresses of your running services.
* **Scraping Metrics:** Once targets are discovered, Prometheus sends HTTP requests (typically to a `/metrics` endpoint) at regular intervals (e.g., every 15 seconds) to "scrape" data.
* **Time-Series Storage:** Collected data is stored as time-series data—meaning metrics are saved as a stream of timestamped values identified by a metric name and key-value pairs called labels.
* **The Pushgateway:** For short-lived or ephemeral microservices (like serverless functions or batch jobs) that don't live long enough to be scraped, Prometheus uses a component called the **Pushgateway**. These jobs push their metrics there, and Prometheus scrapes the gateway.

---

## ✨ Core Features

* **Multi-Dimensional Data Model:** Metrics are identified by a name and a set of key-value pairs (labels). This allows you to slice and dice data easily (e.g., tracking `http_requests_total` specifically for `service="auth"` and `status="500"`).
* **PromQL (Prometheus Query Language):** A powerful, native query language that allows you to aggregate, slice, and calculate rates or trends across your microservices in real time.
* **Autonomous & Single Binary:** Prometheus servers are independent and do not rely on distributed storage or network databases. This ensures that even if your application infrastructure crashes, your monitoring tool stays alive to tell you what failed.
* **Alertmanager:** Handles alerts sent by client applications or Prometheus queries. It manages silencing, inhibition, aggregation, and sends notifications via email, Slack, PagerDuty, or Webhooks.

---

## ⚙️ Configuration Structure

Prometheus is configured using a single YAML file (`prometheus.yml`). The configuration is split into four primary sections:

1. **`global`**: Controls defaults for scraping intervals, timeouts, and evaluation rules.
2. **`rule_files`**: Points to files containing recording rules (pre-calculating expensive queries) and alerting rules (conditions that trigger alerts).
3. **`alerting`**: Configures how Prometheus communicates with the Alertmanager.
4. **`scrape_config`**: Specifies the targets and jobs Prometheus will monitor. This is where you set up static IPs or Service Discovery.

```yaml
global:
  scrape_interval: 15s # Scrape targets every 15 seconds by default.
  evaluation_interval: 15s # Evaluate alerting rules every 15 seconds.

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Example of integrating with a microservice via Kubernetes discovery
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
```

---

## 🤝 Integration into Microservices

To make a microservice observable by Prometheus, you follow a two-step integration process:

### 1. Instrumentation (The Code Level)
You must expose an HTTP endpoint in your code that outputs data in the Prometheus text format. You do this using **Prometheus Client Libraries** (available for Go, Java, Python, Node.js, .NET, etc.). 
* You declare metrics like **Counters** (e.g., total requests received), **Gauges** (e.g., current memory usage), or **Histograms** (e.g., request latency).

### 2. Exporters (The Infrastructure Level)
For third-party systems that you didn't code yourself (like databases or message brokers), you cannot instrument the source code directly. Instead, you deploy an **Exporter** alongside the service. The exporter acts as a translator: it fetches metrics from the service (like MySQL or Redis) and translates them into the Prometheus format for scraping.
* **Common Exporters:** Node Exporter (for Linux host metrics), Blackbox Exporter (for probing endpoints over HTTP/TCP), and Kube-State-Metrics (for Kubernetes cluster stats).

### 3. Visualization
While Prometheus has a basic built-in expression browser for debugging, it is almost universally integrated with **Grafana** to build rich, visual dashboards that track the health of your microservices.


# 📊 Phase 4 Deep Dive: Observability & Alerting with Prometheus

**Goal:** Establish robust monitoring, observability, and automated alerting for the Enterprise Microservices Sandbox. This section details how Prometheus integrates with the Istio Service Mesh to scrape metrics from the Online Boutique microservices and route critical alerts via Alertmanager.

## 🏗️ Core Features & Architecture

In a microservices architecture, monitoring must be dynamic and scalable. Prometheus achieves this through a robust ecosystem:
*   **Pull-Based Data Collection:** Instead of services pushing data, the Prometheus server periodically scrapes HTTP endpoints (e.g., `/metrics`) exposed by the workloads.
*   **Time-Series Database (TSDB):** Metrics are stored as time-series data, identified by metric names and key-value pairs (labels).
*   **Dynamic Target Discovery:** Integrates directly with the Kubernetes API (`kubernetes_sd_configs`) to automatically discover new pods and services as they scale.
*   **PromQL:** A highly flexible query language used to aggregate metrics, calculate percentiles, and define alerting thresholds.

### The Lifecycle of a Metric (Istio Integration)
Because this sandbox utilizes Istio, no application-level code changes were required to expose metrics. The lifecycle flows seamlessly through the Envoy sidecars:
1.  **Metric Generation:** The Istio Envoy sidecar proxy intercepts all pod traffic and automatically generates standard network and HTTP metrics.
2.  **Scraping:** Prometheus scrapes the Envoy endpoint (`http://localhost:15090/stats/prometheus`) every 15 seconds.
3.  **Storage & Evaluation:** Data is written to the TSDB. The evaluation engine continuously runs predefined PromQL rules against this data.
4.  **Alerting:** If an error threshold is breached, Prometheus forwards the event to Alertmanager.
5.  **Notification:** Alertmanager deduplicates, groups, and routes the alert to receivers (e.g., a Slack channel).

## ⚙️ Configuration & Implementation

### 1. Target Discovery & Scraping
Prometheus is configured via a Kubernetes ConfigMap. The `scrape_configs` define how targets are discovered. Using Istio, the configuration relies on `relabel_configs` to filter and target pods that have the Istio proxy injected:

```yaml
# Snippet from prometheus.yml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### 2. Querying with PromQL
During the sandbox implementation, we validated cluster health using the Prometheus expression browser. Key queries used to monitor the Online Boutique include:

1. **Cluster Traffic (RPS):** sum(rate(istio_requests_total[5m])) by (destination_service_name)

2. **Service Latency (95th Percentile):** histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le, destination_service_name))

3. **HTTP 5xx Error Rate:** sum(rate(istio_requests_total{response_code=~"5.."}[5m])) by (destination_service_name)

## 🚨 Alerting with Alertmanager
To automate incident response, we deployed Alertmanager into the istio-system namespace and configured a critical error rate alert.

**Alert Rule Definition**
We added a prometheus.rules block to the Prometheus ConfigMap to trigger an alert if any microservice experiences an HTTP 5xx error rate above 5% for over 1 minute:

```YAML
groups:
- name: boutique-alerts
  rules:
  - alert: HighErrorRate
    expr: sum(rate(istio_requests_total{response_code=~"5.."}[1m])) by (destination_service_name) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High HTTP 5xx error rate detected on {{ $labels.destination_service_name }}"
```
    
**Slack Notification Routing**
Alertmanager was configured to route these critical alerts to a dedicated Slack channel using an Incoming Webhook:

```YAML
route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'destination_service_name']
receivers:
- name: 'slack-notifications'
  slack_configs:
  - channel: '#alerts'
    send_resolved: true
    title: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
    # ... webhook URL configuration ...
```

## 💥 Chaos Testing: Validating the Pipeline
To verify the end-to-end observability pipeline, we performed a controlled failure simulation (Chaos Engineering):

1. **Fault Injection:** Scaled down a critical backend dependency:kubectl scale deployment productcatalogservice --replicas=0

2. **Traffic Generation:** Sent traffic to the frontend to generate 500 Internal Server Errors.

3. **Observation:** Watched the HighErrorRate rule transition from Inactive ➔ Pending ➔ Firing in the Prometheus UI.

4. **Notification:** Confirmed the alert successfully propagated to the Alertmanager UI and fired the payload to the configured Slack receiver.

5. **Resolution:** Restored the deployment (--replicas=1) and verified the automated "RESOLVED" notification in Slack.

Next Step: With metric collection and automated alerting established, the next phase focuses on building dynamic, real-time visualization dashboards using Grafana to plot these PromQL time-series data points.