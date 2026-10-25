---
title: "Grafana and dynamic visualization"
parent: "3. Project 1"
nav_order: 4
---

# Grafana & Prometheus: Architecture, Configuration, and Integration

[Grafana](https://grafana.com/) is an open-source analytics and interactive visualization platform. Unlike [Prometheus](https://prometheus.io/), which collects and stores time-series metrics, Grafana does not store data. Instead, it serves as a visualization layer that queries metrics from Prometheus and transforms them into actionable dashboards and alerts.

---

## Core Grafana Features

* **Custom Dashboards:** Build dynamic visualizations using panels, graphs, gauges, logs, and single-stat blocks.
* **PromQL Support:** Native, deep support for Prometheus Query Language with an interactive autocomplete query editor.
* **Explore Mode:** An ad-hoc workspace to test queries, inspect raw metric data, and troubleshoot issues without saving a dashboard.
* **Alerting Engine:** Set threshold-based alert rules inside Grafana or sync directly with Prometheus Alertmanager.
* **Variables & Templating:** Create dynamic dashboards with dropdown selectors (e.g., filtering by server instance, environment, or namespace).
* **Transformations & Exemplars:** Clean, filter, and organize metrics on the fly, and link metric spikes directly to tracing data.

---

## Grafana Configuration

Grafana is configured via its main configuration file (`grafana.ini`), typically located at `/etc/grafana/grafana.ini` on Linux.

### Key Configuration Block Examples

```ini
[server]
protocol = http
http_port = 3000
domain = localhost

[security]
admin_user = admin
admin_password = admin  # Change immediately upon first login
```

### Declarative Provisioning (Data Sources)
You can programmatically configure data sources using YAML files placed in `/etc/grafana/provisioning/datasources/`:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
```

---

## How Prometheus and Grafana Work Together

1. **Data Collection:** Prometheus pulls (`scrapes`) time-series metrics from target systems or exporters (e.g., Node Exporter on port `9100`) and saves them in its Time Series Database (TSDB).
2. **Querying:** Grafana connects to the Prometheus HTTP API (typically running on `http://localhost:9090`) as a target data source.
3. **Rendering:** When a user opens a dashboard, Grafana sends PromQL queries to Prometheus, receives the raw datasets, and renders them into visual charts.

---

## Step-by-Step Integration Guide

### Step 1: Run via Docker Compose
Create a `docker-compose.yml` file to spin up both services quickly:

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

### Step 2: Configure Prometheus Scrape Targets
Create a basic `prometheus.yml` configuration file:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']
```

### Step 3: Add Prometheus in Grafana
1. Open your browser and navigate to `http://localhost:3000`.
2. Log in with the default credentials (`admin` / `admin`).
3. Navigate to **Connections** > **Data Sources** > **Add data source** and select **Prometheus**.
4. Set the **Prometheus server URL** to `http://prometheus:9090` (if using Docker) or `http://localhost:9090`.
5. Click **Save & test** to verify the connection.

### Step 4: Import an Official Dashboard
Instead of building visuals from scratch, you can instantly import community-created templates:
1. Go to **Dashboards** > **Import**.
2. Enter a dashboard ID (e.g., `1860` for the full Node Exporter dashboard).
3. Select your Prometheus data source and click **Load**.


## 📈 Phase 5: Visualization & Dashboards with Grafana

**Goal:** Transform the raw time-series metrics collected by Prometheus into actionable, real-time visual insights. This phase covers deploying Grafana, connecting the Istio Prometheus data source, and building a dynamic dashboard using PromQL and templating variables.

### 🧩 Core Features in the Observability Stack

While Prometheus excels at scraping and storing data, Grafana is the industry standard for querying and visualizing it. Key features utilized in this sandbox include:
*   **Native Prometheus Integration:** Seamlessly connects to the Prometheus TSDB to execute complex PromQL queries on the fly.
*   **Dynamic Templating:** Uses variables to filter metrics across the entire dashboard without duplicating panels.
*   **Multi-Modal Visualization:** Combines Stat panels for high-level health indicators (like overall RPS) with Time Series graphs for granular latency and error tracking.

### ⚙️ Deployment & Configuration

Grafana was deployed into the `istio-system` namespace using the standard Istio addon manifests, automatically configuring the local Prometheus instance as its default Data Source.

```bash
# Deploy Grafana
kubectl apply -f [https://raw.githubusercontent.com/istio/istio/release-1.21/samples/addons/grafana.yaml](https://raw.githubusercontent.com/istio/istio/release-1.21/samples/addons/grafana.yaml)

# Access the UI
kubectl port-forward svc/grafana 3000:3000 -n istio-system
```

### 📊 Building the "Istio Workload" Dashboard
To monitor the health of the Online Boutique microservices, we constructed a custom dashboard utilizing Envoy proxy metrics (istio_requests_total and istio_request_duration_milliseconds_bucket).

1. **Dynamic Variables (Templating)**
To avoid hardcoding service names and allow dynamic filtering, we configured a dashboard variable named service.

**Query Type:** Label values

**Metric:** istio_requests_total

**Label:** destination_service_name

**Query Executed:** label_values(istio_requests_total, destination_service_name)

Implementation Note: When configuring label filters, it is critical to extract the exact destination_service_name label mapped by Istio to populate the multi-value dropdown correctly.

### 2. Core Telemetry Panels
With the data source and variables configured, we built three foundational panels using PromQL:

**Panel 1: Overall Cluster Traffic (Stat Panel)**
Displays the aggregate Requests Per Second (RPS) across the entire cluster.

```Code snippet
sum(rate(istio_requests_total[5m]))
```

**Panel 2: P95 Latency Distribution (Time Series)**
Tracks the 95th percentile request duration, filtering dynamically based on the $service variable. The legend was cleaned up using the {{destination_service_name}} alias.

```Code snippet
histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{destination_service_name=~"$service"}[5m])) by (le, destination_service_name))
```

### Panel 3: HTTP 5xx Error Rates (Time Series)
Monitors failing requests, providing the visual counterpart to the Alertmanager rules configured in Phase 4.

```Code snippet
sum(rate(istio_requests_total{response_code=~"5..", destination_service_name=~"$service"}[5m])) by (destination_service_name)
```

### 🏁 Observability Pipeline Validation
By integrating Istio, Prometheus, Alertmanager, and Grafana, the local Enterprise Sandbox now features a production-grade observability pipeline.

1. **Envoy generates the metrics.**

2. **Prometheus scrapes and evaluates the rules.**

3. **Alertmanager routes critical thresholds to Slack.**

4. **Grafana** provides the "single pane of glass" to visually correlate traffic spikes with latency degradation and 5xx errors during chaos testing.

## Commands Local testing
kubectl port-forward deployment/frontend 8080:8080
kubectl get configmap prometheus -n istio-system -o yaml > prometheus-cm.yaml 
kubectl apply -f prometheus-cm.yaml
kubectl rollout restart deployment/prometheus -n istio-system
kubectl port-forward svc/prometheus 9090:9090 -n istio-system
kubectl port-forward svc/grafana 3000:3000 -n istio-system
kubectl port-forward svc/alertmanager 9093:9093 -n istio-system
kubectl scale deployment productcatalogservice --replicas=0
kubectl rollout restart deployment/prometheus -n istio-system 
kubectl scale deployment productcatalogservice --replicas=1
kubectl rollout restart deployment/prometheus -n istio-system