# Enterprise Microservices Sandbox: Istio, Online Boutique and AI Agents

**Goal:** Evolve the architecture from standalone AI scripts to a secure, monitored microservices ecosystem. This runbook details how to deploy a local Kubernetes cluster running the Google Cloud Online Boutique microservices demo, secured by an Istio Service Mesh, and integrated with both a Gemini Shopping Assistant and a custom Autonomous AI Agent.

---

## 🏗️ Phase 1: Build the Local Cluster & Istio Service Mesh

To simulate a governed enterprise environment, we use Kind (Kubernetes in Docker) and inject the Istio control plane to manage traffic, security (mTLS), and observability.

### 1. Provision the Sandbox Cluster

```bash
kind create cluster --name enterprise-sandbox
```
### 2. Install Istio Control Plane
Deploy the Istio demo profile and configure the default namespace for automatic sidecar proxy injection.

```Bash
istioctl install --set profile=demo -y
```

Enable automatic Envoy proxy injection for all new pods

```
kubectl label namespace default istio-injection=enabled
```

## 🛍️ Phase 2: Deploy Online Boutique (with Istio + AI Assistant)

We utilize Kustomize to merge the base Online Boutique application, the Istio manifests, and the Gemini AI Shopping Assistant into a single deployment.

### 1. Configure AI Credentials
Store the Gemini API key securely in the cluster as a Kubernetes Secret:

```Bash
kubectl create secret generic gemini-api-key \
  --from-literal=GEMINI_API_KEY="your-actual-api-key-here"
```
### 2. Deploy via Kustomize
Create a temporary kustomization.yaml at the root of the repository to build the required components:

```
YAML
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - kubernetes-manifests/

components:
  - kustomize/components/service-mesh-istio
  - kustomize/components/shopping-assistant
```

Apply the stack and verify the Envoy sidecars (2/2 ready state):

```
Bash
kubectl apply -k .
kubectl get pods -w
```

## 🤖 Phase 3: Deploy the Autonomous AI Agent
Integrate the custom Python GitHub Issue Agent into the service mesh alongside the application workloads.

### 1. Containerize the Agent
Create a Dockerfile for the agent:

```
Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "agent.py"]
```

Build and load the image directly into the local Kind cluster (bypassing external registries):

```
Bash
docker build -t github-issue-agent:v1 .
kind load docker-image github-issue-agent:v1 --name enterprise-sandbox
```

## 2. Deploy the Agent Pod
Apply the Kubernetes Deployment manifest (agent-deployment.yaml):

```
YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: github-issue-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: github-issue-agent
  template:
    metadata:
      labels:
        app: github-issue-agent
    spec:
      containers:
      - name: agent
        image: github-issue-agent:v1
        imagePullPolicy: IfNotPresent
```
```
Bash
kubectl apply -f agent-deployment.yaml
```

## 📊 Phase 4: Service Mesh Telemetry & Observability (Kiali)
To visualize real-time traffic flow, latency, and mTLS encryption between the microservices and the AI pods, we deploy Prometheus and Kiali.

### 1. Install Telemetry Add-ons
```
Bash
kubectl apply -f [https://raw.githubusercontent.com/istio/istio/release-1.21/samples/addons/prometheus.yaml](https://raw.githubusercontent.com/istio/istio/release-1.21/samples/addons/prometheus.yaml)
kubectl apply -f [https://raw.githubusercontent.com/istio/istio/release-1.21/samples/addons/kiali.yaml](https://raw.githubusercontent.com/istio/istio/release-1.21/samples/addons/kiali.yaml)
```

### 2. Generate Application Traffic
Port-forward the frontend to simulate user interactions:

```
Bash
kubectl port-forward deployment/frontend 8080:8080
```
Navigate to http://localhost:8080 to interact with the storefront and Gemini Assistant.

## 3. Access the Kiali Dashboard
Securely tunnel into the Istio visualization dashboard:

```
Bash
istioctl dashboard kiali
```
## Architectural Verification:
In Kiali (Graph > Namespace: default > Display: Traffic Animation & Security), you will see real-time connections between the frontend and the shopping-assistant. The presence of the lock icon confirms that Istio has automatically upgraded local pod-to-pod communication to encrypted Mutual TLS (mTLS).
