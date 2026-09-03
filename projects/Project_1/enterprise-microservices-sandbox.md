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

### Troubleshooting & Incident Ledger

The shoppingassistantservice pod failed to reach a 2/2 Running state out of the box. Below is the chronological ledger of the incidents, root causes, and applied Platform Engineering fixes.

#### Incident 1: Kubernetes OOMKilled
Symptom: kubectl get pods showed the shoppingassistantservice pod crashing with OOMKilled (Exit Code 137).

Root Cause: The underlying Docker Desktop WSL 2 backend lacked sufficient dynamic memory allocation to host the Python/Gemini runtime alongside the rest of the cluster.

Resolution: Injected a .wslconfig file into the Windows user profile to dedicate resources, and restarted the WSL engine.

```
PowerShell
Set-Content -Path "$env:USERPROFILE\.wslconfig" -Value "[wsl2]`nmemory=6GB`nprocessors=4`nswap=2GB"
wsl --shutdown
```

#### Incident 2: Python 3.14 Dependency Crash (CrashLoopBackOff)
Symptom: Pod entered a crash loop. Container logs revealed ModuleNotFoundError: No module named 'aiohttp' and Pydantic v1 compatibility warnings.

Root Cause: The original Dockerfile used a floating Python tag that automatically pulled 3.14, which broke LangChain dependencies.

Resolution:

Pinned the Dockerfile base image to FROM python:3.11-slim.

Updated the multi-stage copy path to /usr/local/lib/python3.11/.

Appended aiohttp to requirements.txt.

#### Incident 3: Cloud Credential Failures (GCP Secret Manager & AlloyDB)
Symptom: Logs revealed google.auth.exceptions.DefaultCredentialsError.

Root Cause: The application was hardcoded to authenticate with Google Cloud Secret Manager (to fetch a database password) and Google Cloud AlloyDB (for vector search). Our local Kind sandbox lacked GCP Application Default Credentials.

Resolution: Patched the source code (shoppingassistantservice.py) to mock cloud dependencies for local execution:

Commented out the secretmanager_v1 client and injected the database password via local OS environment variables.

Commented out AlloyDBEngine and replaced the real database connection with a custom MockVectorStore and MockRetriever class that safely returned empty arrays for RAG queries.

#### Incident 4: 500 Internal Server Error (KeyError: 'image')
Symptom: The pod reached 2/2 Running, but sending a text-only "Hello" message in the frontend chat resulted in a silent UI failure and a 500 error in the pod logs (KeyError: 'image').

Root Cause: The Python API endpoint was rigidly expecting an image payload in every JSON request and lacked fault tolerance for text-only messages.

Resolution: Refactored the talkToGemini route to handle the image dynamically using .get('image').

Python
content_list = [{"type": "text", "text": "Your prompt..."}]
image_data = request.json.get('image')
if image_data:
    content_list.append({"type": "image_url", "image_url": image_data})
message = HumanMessage(content=content_list)
Incident 5: Google API 400 INVALID_ARGUMENT (Hardcoded Override)
Symptom: LangChain successfully compiled the request but the Gemini API rejected it with API key not valid.

Root Cause: The base Kubernetes Deployment manifest had GOOGLE_API_KEY=GOOGLE_API_KEY_VAL explicitly hardcoded in the container spec. This hardcoded value took precedence over the valid credentials injected via our gemini-api-key Secret.

Resolution: Forcefully overwrote the specific environment variable directly in the deployment using kubectl set env, which bypassed the manifest hardcode and triggered a rolling restart.

```
PowerShell
kubectl set env deployment/shoppingassistantservice GOOGLE_API_KEY="<ACTUAL_VALID_KEY>"
🔄 Standard Rebuild Cycle Used
For every source code or Dockerfile patch above, we used the following local deployment loop to bypass external registries:

PowerShell
docker build -t shoppingassistantservice:local ./src/shoppingassistantservice
kind load docker-image shoppingassistantservice:local --name enterprise-sandbox
kubectl delete pod -l app=shoppingassistantservice
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

## Phase 3 Troubleshooting & Incident Ledger
The agent integration revealed several containerization and orchestration challenges. Below are the incidents and the applied Platform Engineering fixes.

### Incident 1: Missing Python Dependency
Symptom: The container crashed immediately with ModuleNotFoundError: No module named 'google'.

Root Cause: The google-cloud-logging package (used for MLOps telemetry) was imported in the script but missing from requirements.txt.

Resolution: Appended google-cloud-logging to the requirements file and rebuilt the Docker image.

### Incident 2: Local LLM Network Routing (Connection Refused)
Symptom: The agent logged httpx.ConnectError: [Errno 111] Connection refused when trying to connect to the Ollama LLM.

Root Cause: The Python script defaulted to http://localhost:11434. Inside the Kubernetes pod, localhost refers to the container itself, not the Windows host machine where Ollama was actually running.

Resolution:

Configured the Windows host environment variable OLLAMA_HOST=0.0.0.0 to accept external traffic.

Patched the Python code to route traffic out of the pod directly to the Docker host network using Docker's internal DNS:

```
Python
ollama_url = os.environ.get("OLLAMA_BASE_URL", "[http://host.docker.internal:11434](http://host.docker.internal:11434)")
llm = ChatOllama(model="llama3", base_url=ollama_url)
```

### Incident 3: Kubernetes Lifecycle Mismatch (CrashLoopBackOff)
Symptom: The agent successfully executed its task, but Kubernetes repeatedly marked the pod with CrashLoopBackOff.

Root Cause: The agent was initially deployed using a Kubernetes Deployment object. Deployments expect container processes to run indefinitely (like a web server). When the Python script finished and exited cleanly, the Deployment controller viewed it as a failure and forcefully restarted it.

Resolution: Deleted the Deployment and converted the manifest to a Kubernetes Job (kind: Job), which gracefully handles scripts designed to run once and terminate.

### Incident 4: Istio Sidecar Zombie Pod (1/2 NotReady)
Symptom: After converting to a Job, the Python script ran perfectly, but the pod hung in a 1/2 NotReady state instead of transitioning to Completed.

Root Cause: The Istio control plane automatically injected an Envoy proxy sidecar (container 2) into the pod. Envoy is a background web server that runs indefinitely. When the Python agent (container 1) finished, the Envoy proxy stayed alive, preventing the pod from fully terminating.

Resolution: Added a pod annotation to explicitly instruct Istio to ignore this specific batch job, preventing the sidecar injection:

```
YAML
annotations:
  sidecar.istio.io/inject: "false"
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
