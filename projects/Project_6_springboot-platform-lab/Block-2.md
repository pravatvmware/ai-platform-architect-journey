---
layout: default
title: Block 2: Deploy to kind, then Helm, then Istio
parent: 8. Spring Boot Platform Lab
nav_order: 4
---

Block 2: Deploy to kind, then Helm, then Istio

Your output confirms Block 1 works. The 395a9444539b is the container ID, because HOSTNAME inside a container is its ID. In Kubernetes the same code will print the pod name, so we’ll see load balancing across replicas.

Block 2 has three parts. We’ll do Part A now and move on when you confirm it works.

Part	What	Why it matters
A	Plain manifests: Deployment, Service, probes, graceful shutdown	Understand every field before Helm hides it
B	Convert to a Helm chart with values per environment	Chart authoring and values management
C	Istio: sidecar injection, Gateway, VirtualService	Ingress and mesh behavior with Spring Boot
Part A: Plain Kubernetes (about 45 min)
A0. Pre-flight
powershell
kind get clusters
kubectl config current-context
kubectl get nodes
kubectl get pods -n istio-system

Note your cluster name (often kind, and the context is kind-<name>). You need it for the next step. Also check that istio-ingressgateway appears in istio-system. If it doesn’t, tell me, because Part C changes slightly.

A1. Load the image into kind

kind nodes are containers with their own image store, so they can’t see images in your Docker Desktop. You must load them:

powershell
kind load docker-image demo:1 --name <your-cluster-name>
docker exec <your-cluster-name>-control-plane crictl images | Select-String demo

The second command proves the image is inside the node. If it’s missing later, the pod shows ErrImagePull or ImagePullBackOff, and the cause is almost always this step. Also note that kind can only use a local image if the tag isn’t :latest, which is why we use demo:1 and imagePullPolicy: IfNotPresent.

A2. Create the manifests

In your lab repo, create deploy/k8s/demo.yaml:

yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo
  namespace: demo
  labels:
    app: demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app: demo
    spec:
      terminationGracePeriodSeconds: 45
      containers:
        - name: demo
          image: demo:1
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: dev
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              memory: 768Mi
          startupProbe:
            httpGet:
              path: /actuator/health/liveness
              port: http
            periodSeconds: 5
            failureThreshold: 30
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: http
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: http
            periodSeconds: 10
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "5"]
---
apiVersion: v1
kind: Service
metadata:
  name: demo
  namespace: demo
spec:
  selector:
    app: demo
  ports:
    - name: http
      port: 80
      targetPort: http

Understand each part (write it in your own words in the doc):

maxUnavailable: 0, maxSurge: 1: a new pod must become Ready before an old one is removed, so capacity never drops during a rollout.
Startup probe: gives the JVM up to 30 × 5 = 150 s to boot. Until it passes, liveness and readiness don’t run, so a slow starter isn’t killed.
Liveness vs readiness: the paths are the two Actuator groups from Block 1.
Requests vs limits: the memory request is 512Mi and the limit is 768Mi. With MaxRAMPercentage=75, the heap is about 576 MB, and the remaining ~190 MB is headroom for non-heap memory.
Graceful shutdown chain: preStop sleeps 5 s (so endpoint removal propagates), then SIGTERM, then Spring drains for up to 30 s. terminationGracePeriodSeconds: 45 covers 5 + 30 with margin.
The Service maps port 80 to the named container port http.
A3. Deploy and watch
powershell
kubectl apply -f deploy/k8s/demo.yaml
kubectl get pods -n demo -w

Watch the pods go 0/1 Running and then 1/1 Running. The delay between those is the startup and readiness probes working. Stop watching with Ctrl+C. Then:

powershell
kubectl get deploy,rs,pods,svc,endpoints -n demo
kubectl describe pod -n demo -l app=demo | Select-String -Pattern "Probe|Limits|Requests|Image:"

Understand: the chain Deployment → ReplicaSet → Pods, and that the Endpoints object lists only the pods that are Ready. This is exactly how readiness controls traffic.

A4. Reach it and see load balancing
powershell
kubectl port-forward -n demo svc/demo 8081:80

In a second PowerShell window:

powershell
1..10 | ForEach-Object { Invoke-RestMethod http://localhost:8081/hello }

Caution: port-forward connects to one pod and sticks with it, so you’ll likely see the same name every time. That’s a port-forward trait, not a Service problem. To see real balancing, call the Service from inside the cluster:

powershell
kubectl run curl -n demo --rm -it --image=curlimages/curl --restart=Never -- sh -c "for i in 1 2 3 4 5 6; do curl -s http://demo/hello; echo; done"

You should see both pod names. (This pod gets an Istio sidecar later if you label the namespace, which is why we use a plain namespace for now.)

A5. Check the app’s own view of itself
powershell
Invoke-RestMethod http://localhost:8081/actuator/health/readiness
(Invoke-WebRequest http://localhost:8081/actuator/prometheus).Content.Split("`n") | Select-Object -First 15
kubectl logs -n demo deploy/demo --tail=20
A6. Prove graceful rollout

This is the interview-worthy test. In one window, run a continuous request loop:

powershell
while ($true) { try { (Invoke-WebRequest http://localhost:8081/hello -TimeoutSec 2).StatusCode } catch { "FAIL" }; Start-Sleep -Milliseconds 300 }

Because port-forward pins to one pod, it may break when that pod is replaced, which would mislead you. A fairer test uses an in-cluster loop:

powershell
kubectl run loadgen -n demo --image=curlimages/curl --restart=Never -- sh -c "while true; do curl -s -o /dev/null -w '%{http_code}\n' http://demo/hello; sleep 0.3; done"

Trigger a rollout in another window, then check the load generator’s output:

powershell
kubectl rollout restart deploy/demo -n demo
kubectl rollout status deploy/demo -n demo
kubectl logs loadgen -n demo | Group-Object | Select-Object Name, Count

Expected: all 200. Any 000, 502, or 503 means requests were dropped. This is your evidence that the readiness gating, preStop, and graceful shutdown work. (Optional experiment: remove the preStop block and graceful setting, repeat, and see whether errors appear. It’s a great line for the doc.)

Clean up the load generator: kubectl delete pod loadgen -n demo

Part A checkpoint

You should be able to explain:

Why did kind load docker-image have to be run?
What does the Endpoints list show, and what happens to it when a readiness probe fails?
Why maxUnavailable: 0?
Why does the terminationGracePeriodSeconds have to be bigger than preStop plus the Spring shutdown timeout?
Why did port-forward not show load balancing?
Document it

Create 02-kind-helm-istio.md in your Pages repo, with a section “Part A: Plain manifests” containing the real outputs for: kubectl get deploy,rs,pods,svc,endpoints, the in-cluster curl loop showing both pod names, and the rollout test result. Commit the manifest and tag:

powershell
git add deploy/k8s/demo.yaml
git commit -m "block2: plain k8s manifests with probes and graceful shutdown"
What to send me

Paste:

The A0 output (cluster name, nodes, whether istio-ingressgateway is present)
The kubectl get ... output from A3
The in-cluster curl output from A4 and the result from A6
Any error text

Then I’ll move you to Part B (Helm chart), where we turn this YAML into a parameterized chart with values-dev.yaml and values-prod.yaml.