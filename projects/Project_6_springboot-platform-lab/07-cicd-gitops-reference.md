---
layout: default
title: cicd gitops reference
parent: 8. Spring Boot Platform Lab
nav_order: 11
---

{% raw %}

# 07: CI/CD and GitOps reference

**Repo:** [pravatvmware/Spring-Boot-Platform-Lab](https://github.com/pravatvmware/Spring-Boot-Platform-Lab)
**Scope:** Blocks 1 to 3 as built: Spring Boot app, Docker image, GitHub Actions, GHCR, Helm, Istio, and the commit-to-deploy flow.
**Audience:** me, three ways: as the **implementing engineer** (commands and config), as the **DevOps architect** (why it is shaped this way), and as the **security reviewer** (what protects what, and what is still a lab shortcut).

How to read this page: every section says what is **implemented in the lab** and what the **production standard** adds. Anything under "Production standard" is not built yet. Do not claim it as done.

---

## 1. Architecture at a glance

```
 Developer
    |  git push (main)
    v
 GitHub repo  pravatvmware/Spring-Boot-Platform-Lab
    |  triggers workflow .github/workflows/ci.yml   (paths filter: demo/**)
    v
 +---------------------------- job: build -----------------------------+
 |  checkout -> setup-java 21 (+Maven cache) -> mvn verify (tests)      |
 |  -> buildx -> login ghcr.io (GITHUB_TOKEN) -> build & push image     |
 |  tags: <full commit SHA>, main                                       |
 +----------------------------------------------------------------------+
    |  needs: build
    v
 +------------------------- job: update-deploy ------------------------+
 |  yq sets .image.tag = <SHA> in deploy/helm/demo/values-dev.yaml      |
 |  commit as github-actions[bot] -> push to main                       |
 +----------------------------------------------------------------------+
    |  Git now records exactly which SHA is deployed to dev
    v
 Engineer (today)   : git pull -> helm upgrade ...   (manual)
 Argo CD (later)    : watches Git -> reconciles the cluster (automatic)
    v
 kind cluster "enterprise-sandbox"
    namespace demo (istio-injection=enabled)
    Deployment demo (app container + istio-proxy sidecar)
    Secret ghcr-pull  --> kubelet pulls image from ghcr.io
    Istio ingress gateway --> VirtualService --> Service demo --> pods
    PeerAuthentication STRICT (mTLS inside the mesh)
```

### Core principle

**CI never touches the cluster.** CI builds an artifact and changes Git. Something else (a human running Helm today, Argo CD later) applies Git to the cluster. This gives:

| Property | Why it matters |
|---|---|
| Git is the source of truth | Audit trail, review, easy rollback with `git revert` |
| No cluster credentials in CI | A compromised pipeline cannot directly change the cluster |
| Immutable image tag (commit SHA) | Any running pod maps to exactly one commit |
| Same image promoted everywhere | You deploy what you tested, no rebuild per environment |

---

## 2. Repo layout and naming standard

```
Spring-Boot-Platform-Lab/
  README.md
  .gitignore
  .github/workflows/ci.yml          pipeline (build + update-deploy)
  demo/                             Spring Boot project
    pom.xml
    Dockerfile
    .dockerignore
    src/main/java/com/example/demo/ DemoApplication.java, HelloController.java
    src/main/resources/application.yml
  deploy/
    k8s/demo.yaml                   plain manifests (learning baseline)
    helm/demo/                      Helm chart
      Chart.yaml
      values.yaml                   defaults
      values-dev.yaml               dev overrides (CI rewrites image.tag here)
      values-prod.yaml              prod overrides
      templates/_helpers.tpl, deployment.yaml, service.yaml
    istio/gateway.yaml              Gateway + VirtualService
    istio/peer-authentication.yaml  STRICT mTLS
```

| Thing | Name | Rule |
|---|---|---|
| Kubernetes namespace | `demo` | one namespace per app/team boundary |
| Helm release | `demo` | with chart `demo`, the fullname helper yields Service `demo` (not `demo-demo`) |
| Image | `ghcr.io/pravatvmware/spring-boot-platform-lab/demo` | **all lowercase**, GHCR rejects uppercase |
| Image tags | full commit SHA, plus `main` | deploy by SHA only; `main` is a convenience pointer |
| Pull secret | `ghcr-pull` | type `kubernetes.io/dockerconfigjson`, same namespace as the pods |
| Git tags | `block-N-done` | one per finished block, docs link to them |
| Commit messages | `blockN: ...`, `ci: deploy demo <sha7> to dev` | the bot uses the `ci:` prefix |
| Istio hosts | `demo.local` (gateway host), `demo.demo.svc.cluster.local` (destination) | |

---

## 3. The application (Block 1)

`HelloController` returns `Hello from <HOSTNAME>`. In Kubernetes `HOSTNAME` is the pod name, so repeated calls prove load balancing.

`demo/src/main/resources/application.yml`:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  endpoint:
    health:
      probes:
        enabled: true
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

| Setting | Effect | Operations reason |
|---|---|---|
| `exposure.include` | Only three Actuator endpoints are reachable | Never expose `*` in production: `env`, `heapdump` and others leak secrets |
| `probes.enabled` | Adds `/actuator/health/liveness` and `/readiness` | Targets for kubelet probes |
| `server.shutdown: graceful` | Drains in-flight requests on SIGTERM | Zero dropped requests on rollout |
| `/actuator/prometheus` | Micrometer metrics | Scraped by Prometheus |

### Dockerfile (`demo/Dockerfile`)

```dockerfile
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B -q dependency:go-offline
COPY src ./src
RUN mvn -B -q package -DskipTests

FROM eclipse-temurin:21-jre
RUN useradd -r -u 1001 app
USER 1001
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-XX:MaxRAMPercentage=75","-jar","app.jar"]
```

| Decision | Reason | Security angle |
|---|---|---|
| Multi-stage | Runtime image has only JRE and the JAR | No compiler or build tools to abuse, fewer CVEs |
| `pom.xml` before `src` | Dependency layer is cached | Faster CI, and fewer downloads from the internet |
| `USER 1001` (numeric) | Non-root | `runAsNonRoot` can be verified by the kubelet; limits blast radius |
| `MaxRAMPercentage=75` | Heap follows the container limit | Avoids OOMKilled when limits change |
| `.dockerignore` (`target`, `.git`) | Keeps context small | Avoids leaking `.git` history into build context |

**Production standard (not yet in lab):** pin base images by digest, build from a minimal or distroless runtime image, scan with Trivy or Grype as a failing gate, generate an SBOM, sign the image.

---

## 4. The pipeline (Block 3)

### 4.1 Final `.github/workflows/ci.yml`

```yaml
name: ci

on:
  push:
    branches: [main]
    paths:
      - "demo/**"
      - ".github/workflows/ci.yml"
  pull_request:
    paths:
      - "demo/**"

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  IMAGE: ghcr.io/pravatvmware/spring-boot-platform-lab/demo   # must be lowercase

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "21"
          cache: maven
          cache-dependency-path: demo/pom.xml

      - name: Build and test
        working-directory: demo
        run: mvn -B -ntp verify

      - uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        if: github.event_name == 'push'
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: demo
          push: ${{ github.event_name == 'push' }}
          tags: |
            ${{ env.IMAGE }}:${{ github.sha }}
            ${{ env.IMAGE }}:main
          cache-from: type=gha
          cache-to: type=gha,mode=max

  update-deploy:
    needs: build
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    env:
      SHA: ${{ github.sha }}
    steps:
      - uses: actions/checkout@v4

      - name: Set image tag in dev values
        run: yq -i '.image.tag = strenv(SHA)' deploy/helm/demo/values-dev.yaml

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add deploy/helm/demo/values-dev.yaml
          git diff --cached --quiet || {
            git commit -m "ci: deploy demo ${SHA::7} to dev"
            git pull --rebase origin main
            git push origin main
          }
```

### 4.2 Line-by-line logic

| Element | What it does | Why |
|---|---|---|
| `on.push.paths` | Runs only when `demo/**` or the workflow file changes | Docs or `deploy/**` commits do not trigger a build |
| The bot commit changes only `deploy/**` | Not in `paths` | **No infinite loop**; also `GITHUB_TOKEN` pushes never trigger workflows |
| `on.pull_request` | Build and test, no push | Unreviewed code never reaches the registry; fork PRs have no write token |
| Workflow `permissions: contents: read` | Default for every job | Least privilege |
| Job `packages: write` (build only) | Allows pushing to GHCR | Only the job that needs it gets it |
| Job `contents: write` (update-deploy only) | Allows the bot commit | Build job cannot write to the repo |
| `concurrency` | Cancels superseded runs on the same ref | Saves minutes, avoids races |
| `cache: maven` | Caches `~/.m2` | Faster builds |
| `working-directory: demo` on the Maven step only | Maven runs in `demo/`; Docker uses `context: demo` | A job-wide default would not affect `uses:` steps and confuses people |
| `if: github.event_name == 'push'` on login | PRs never authenticate to the registry | |
| Tags `<sha>` and `main` | SHA is immutable and traceable | Never deploy `main` or `latest` |
| `cache-from/to: type=gha` | Docker layer cache across runs | |
| `needs: build` | `update-deploy` runs only if build, tests and push succeeded | A tag in Git can never point at a missing image |
| `strenv(SHA)` in `yq` | Value stays a string | A SHA of only digits would otherwise parse as a number |
| `git diff --cached --quiet \|\|` | Skips commit if nothing changed | Re-runs do not fail |
| `git pull --rebase` | Handles a push that landed during the job | |

### 4.3 Credentials in this pipeline

| Credential | Where it lives | Lifetime | Used for |
|---|---|---|---|
| `GITHUB_TOKEN` | Created per run by GitHub | Ends with the job, scoped by `permissions:` | GHCR push, bot commit |
| Cluster credentials | **Not in CI at all** | | CI cannot deploy directly |
| Registry pull PAT | Kubernetes Secret `ghcr-pull` in namespace `demo` | Long-lived (classic PAT) | kubelet pulls a private image |

**Production standard:** workflows pinned to commit SHAs (not tags), OIDC to the cloud or Vault for any external credential, environments with required reviewers for prod, a GitHub App token (not a PAT) for cross-repo writes, and branch protection (see section 9).

---

## 5. The Helm chart

### 5.1 `Chart.yaml`

```yaml
apiVersion: v2
name: demo
description: Spring Boot demo service
type: application
version: 0.1.0        # chart version: bump when templates change
appVersion: "1"       # describes the application being deployed
```

### 5.2 `values.yaml` (defaults)

```yaml
replicaCount: 2

image:
  repository: ghcr.io/pravatvmware/spring-boot-platform-lab/demo
  tag: "1"
  pullPolicy: IfNotPresent

imagePullSecrets: []

springProfile: dev

service:
  port: 80

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    memory: 768Mi

probes:
  startup:
    failureThreshold: 30
    periodSeconds: 5
  readiness:
    periodSeconds: 10
  liveness:
    periodSeconds: 10

terminationGracePeriodSeconds: 45
preStopSleepSeconds: 5
```

### 5.3 Environment overrides

`values-dev.yaml` (CI changes only the `tag` line):

```yaml
replicaCount: 1
springProfile: dev
image:
  tag: "<full commit SHA written by CI>"
imagePullSecrets:
  - name: ghcr-pull
resources:
  requests: {cpu: 100m, memory: 512Mi}
  limits: {memory: 768Mi}
```

`values-prod.yaml`:

```yaml
replicaCount: 3
springProfile: prod
resources:
  requests: {cpu: 500m, memory: 768Mi}
  limits: {memory: 1Gi}
```

Precedence: `values.yaml` < `-f values-<env>.yaml` < `--set`. Maps merge by key, lists are replaced whole.

### 5.4 `templates/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "demo.fullname" . }}
  labels:
    {{- include "demo.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "demo.selectorLabels" . | nindent 6 }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        {{- include "demo.selectorLabels" . | nindent 8 }}
    spec:
      terminationGracePeriodSeconds: {{ .Values.terminationGracePeriodSeconds }}
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: demo
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: {{ .Values.springProfile | quote }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          startupProbe:
            httpGet:
              path: /actuator/health/liveness
              port: http
            periodSeconds: {{ .Values.probes.startup.periodSeconds }}
            failureThreshold: {{ .Values.probes.startup.failureThreshold }}
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: http
            periodSeconds: {{ .Values.probes.readiness.periodSeconds }}
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: http
            periodSeconds: {{ .Values.probes.liveness.periodSeconds }}
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "{{ .Values.preStopSleepSeconds }}"]
```

`templates/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "demo.fullname" . }}
  labels:
    {{- include "demo.labels" . | nindent 4 }}
spec:
  selector:
    {{- include "demo.selectorLabels" . | nindent 4 }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
```

### 5.5 Why the Deployment is built this way

| Setting | Failure it prevents |
|---|---|
| `maxUnavailable: 0`, `maxSurge: 1` | Capacity drop during rollout; a failing new pod never replaces a working one |
| `startupProbe` (30 x 5s) | Slow JVM boot being killed by liveness |
| readiness on `/actuator/health/readiness` | Traffic reaching a pod that is not ready |
| liveness on `/actuator/health/liveness` (no DB check) | A DB outage restarting every pod |
| `preStop: sleep 5` | SIGTERM arriving before endpoint removal has propagated |
| `terminationGracePeriodSeconds: 45` | SIGKILL during drain (5s preStop + 30s Spring drain + margin) |
| Memory request 512Mi, limit 768Mi, `MaxRAMPercentage=75` | Heap about 576 MB, leaves headroom, avoids OOMKilled |
| Image tag from values | One chart for every environment, CI changes one line |

**Production standard (not yet in lab):** add to the pod spec

```yaml
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: demo
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true     # needs a writable /tmp emptyDir for Spring
            capabilities:
              drop: ["ALL"]
```

plus a PodDisruptionBudget, an HPA, topology spread across nodes, a `ServiceMonitor`, and a NetworkPolicy. Validate with `helm lint`, `helm template`, `kubeconform` and a policy check (Kyverno or OPA) in CI.

---

## 6. Istio (Block 2C)

`deploy/istio/gateway.yaml`:

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: demo-gateway
  namespace: demo
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "demo.local"
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: demo
  namespace: demo
spec:
  hosts:
    - "demo.local"
  gateways:
    - demo-gateway
  http:
    - route:
        - destination:
            host: demo.demo.svc.cluster.local
            port:
              number: 80
```

`deploy/istio/peer-authentication.yaml`:

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: demo
spec:
  mtls:
    mode: STRICT
```

| Concept | Meaning |
|---|---|
| Namespace label `istio-injection=enabled` | A webhook injects `istio-proxy` at pod creation, so pods must be restarted after labelling |
| `2/2` READY | App container plus sidecar |
| Gateway | Opens port and host on the ingress proxy ("the door") |
| VirtualService | Routing rules bound to the Gateway ("where it goes") |
| `Host: demo.local` header | Selects the route; wrong host gives 404 |
| 503 with a valid host | Route matched but upstream missing (the `demo-demo` vs `demo` bug) |
| Probe rewrite | Istio routes kubelet probes via port 15020 so they work under STRICT mTLS |
| STRICT | Plain HTTP from a pod outside the mesh is reset (proved with the `outsider` namespace) |
| Gateway Service `<pending>` | kind has no cloud load balancer, reach it with `kubectl port-forward` |

**Production standard (not yet in lab):** HTTPS on the gateway (port 443, TLS from cert-manager), a default-deny `AuthorizationPolicy` plus explicit allows by service account, JWT validation with Keycloak via `RequestAuthentication`, and gateway rate limiting.

---

## 7. Registry access and `imagePullSecrets`

The kubelet, not the app, pulls images. For a private GHCR package it needs credentials.

Create the secret (token never lands in shell history or Git):

```powershell
$env:GHCR_PAT = Read-Host "Paste PAT"
kubectl create secret docker-registry ghcr-pull -n demo `
  --docker-server=ghcr.io `
  --docker-username=pravatvmware `
  --docker-password=$env:GHCR_PAT
Remove-Item Env:GHCR_PAT
```

The PAT is a **classic** token with only `read:packages`.

| Rule | Detail |
|---|---|
| Same namespace | A pod can reference only secrets in its own namespace |
| Registry host must match | Secret key `ghcr.io` for an image starting with `ghcr.io/` |
| `IfNotPresent` | A cached image never triggers auth, so one node can work while another fails |
| Changing the secret | Does not restart running pods |
| Base64 is not encryption | Restrict RBAC and enable etcd encryption at rest |

| Event message | Meaning |
|---|---|
| `unauthorized` / `denied` / 401 | Missing, wrong or expired credentials, or secret not referenced |
| `manifest unknown` / `not found` | Tag or image does not exist (CI did not push it) |
| `repository does not exist` on docker.io | Image name has no registry host |
| `no match for platform` | CPU architecture mismatch |

**Production standard:** no personal PAT. Use a read-only robot or service credential, stored in Vault, synced into each namespace by External Secrets Operator (or a Kyverno generate policy), with rotation and an alert on pull failures. On EKS or AKS use node identity (IAM role for ECR, managed identity for ACR) so no secret exists at all.

---

## 8. End-to-end flow: step by step with commands

### 8.1 One-time setup

```powershell
# cluster tooling check
kubectl config current-context          # kind-enterprise-sandbox
kubectl get pods -n istio-system        # istiod + gateways Running

# namespace in the mesh
kubectl create namespace demo
kubectl label namespace demo istio-injection=enabled

# pull secret (section 7)
# Istio resources
kubectl apply -f deploy/istio/gateway.yaml
kubectl apply -f deploy/istio/peer-authentication.yaml
```

GitHub settings: repo **Settings, Actions, General, Workflow permissions: Read and write**. Package visibility **Private** if you want to use the pull secret.

### 8.2 Every change

| # | Action | Command or place | What happens |
|---|---|---|---|
| 1 | Edit code | `demo/...` | |
| 2 | Commit and push | `git add demo; git commit -m "feat: ..."; git push origin main` | Workflow starts |
| 3 | `build` job | Actions tab | Tests, image built, pushed as `<sha>` and `main` |
| 4 | `update-deploy` job | Actions tab | Bot commits the new SHA into `values-dev.yaml` |
| 5 | Sync local copy | `git pull` | **Required**, the bot pushed a commit you do not have |
| 6 | Confirm tag | `Select-String "tag:" deploy/helm/demo/values-dev.yaml` | Full SHA visible |
| 7 | Deploy | `helm upgrade demo deploy/helm/demo -n demo -f deploy/helm/demo/values-dev.yaml` | Rolling update |
| 8 | Wait | `kubectl rollout status deploy/demo -n demo` | |
| 9 | Verify | commands in 8.3 | |

Step 7 is the only manual step. Argo CD removes it by watching `deploy/helm/demo` and syncing automatically.

### 8.3 Verification checklist

```powershell
kubectl get pods -n demo                                   # 2/2 Running
kubectl get pod -n demo -o jsonpath="{.items[0].spec.containers[?(@.name=='demo')].image}"
kubectl get pod -n demo -o jsonpath="{.items[0].spec.imagePullSecrets}"
kubectl describe pod -n demo -l app=demo | Select-String "Pulling|Pulled|Started"
helm list -n demo ; helm history demo -n demo
istioctl proxy-status | Select-String "demo|ingressgateway"
istioctl analyze -n demo
kubectl port-forward -n istio-system svc/istio-ingressgateway 8088:80      # separate window
Invoke-RestMethod http://localhost:8088/hello -Headers @{Host="demo.local"}
```

| Check | Pass condition |
|---|---|
| Image | `ghcr.io/pravatvmware/.../demo:<full SHA>` matching the latest bot commit |
| Pod | `2/2 Running`, restarts 0 |
| `Pulled` event | Node downloaded from GHCR |
| `proxy-status` | `SYNCED` |
| `analyze` | No errors |
| Gateway call | `Hello from demo-...` |

### 8.4 Zero-downtime proof

```powershell
kubectl run loadgen -n demo --image=curlimages/curl --restart=Never -- sh -c "while true; do curl -s -o /dev/null -w '%{http_code}\n' http://demo/hello; sleep 0.3; done"
Start-Sleep 15
helm upgrade demo deploy/helm/demo -n demo -f deploy/helm/demo/values-dev.yaml
kubectl rollout status deploy/demo -n demo
kubectl logs loadgen -n demo | Group-Object | Select-Object Name, Count
kubectl delete pod loadgen -n demo
```

Pass: only `200`. Earlier result: 1550 requests, all 200, across a rolling restart. (The `loadgen` pod runs inside the mesh namespace, so with STRICT mTLS it works because it has a sidecar.)

### 8.5 Rollback

| Method | Command | Note |
|---|---|---|
| GitOps (preferred) | `git revert <bot commit>`, push, then `helm upgrade` (or Argo syncs) | Git stays the truth |
| Helm | `helm rollback demo <revision> -n demo` | Creates a **new** revision; Git is now out of date, drift |
| Kubernetes | `kubectl rollout undo deploy/demo -n demo` | Same drift caveat |

---

## 9. Architect view: lab vs production

| Concern | Lab (as built) | Production standard |
|---|---|---|
| Repo model | Code and deploy config in one repo | Separate app repo and deployment repo; pipeline opens a PR to the deployment repo |
| Delivery | `helm upgrade` by hand | Argo CD (or Flux) with `ApplicationSet` per environment, auto-sync + selfHeal in dev, manual sync or approval for prod |
| Promotion | Dev only | Same SHA promoted dev, staging, prod by PR; no rebuild |
| Dev write path | Bot pushes directly to `main` | Bot opens a PR; auto-merge for dev, required reviewers (CODEOWNERS) for prod; branch protection on `main` |
| Environments | `values-dev`, `values-prod` files | GitHub Environments with protection rules and environment-scoped secrets |
| Cluster | Single kind cluster | Separate clusters or strong namespace isolation per environment, IaC for clusters (Terraform) |
| Secrets | PAT in a Kubernetes Secret | Vault + External Secrets Operator, dynamic or short-lived credentials, etcd encryption |
| Ingress | HTTP on port 80 via port-forward | HTTPS with cert-manager, API gateway, WAF, rate limits |
| Observability | Prometheus and Kiali exist | ServiceMonitor, Grafana dashboards, alerts on error rate, latency, saturation, cert expiry; centralized logs |
| Scale and HA | 1 to 3 replicas | HPA, PDB, topology spread, multi-zone nodes |
| Governance | None | Policy as code (Kyverno or OPA Gatekeeper), image signature verification, SLO and runbooks |
| Rollback | Manual | `git revert` reconciled by Argo CD; alert on sync failure |

### Deployment topology decision (talking point)

> "I keep the pipeline push-based for artifacts and pull-based for deployment. CI builds, tests, scans and publishes an immutable image, then records the desired version in Git. A GitOps controller in the cluster pulls from Git. That keeps cluster credentials out of CI, gives a full audit trail, and makes rollback a revert."

---

## 10. Security view

### 10.1 Threat model

| Threat | Where it could happen | Mitigation in lab | Production standard |
|---|---|---|---|
| Malicious PR pushes an image | CI | PRs build and test only, no registry login, no push | Required review, fork PRs without secrets, never use `pull_request_target` with untrusted code |
| Compromised third-party action | CI | Official `actions/*` and `docker/*` actions only | Pin every action to a full commit SHA, use Dependabot for action updates |
| Token theft from CI | CI | `GITHUB_TOKEN` is per-run and least-privilege per job | OIDC for external systems, no stored long-lived secrets, audit workflow changes |
| Tampered or swapped image | Registry | Deploy by immutable SHA tag | Pin by digest, sign with cosign (keyless via OIDC), verify at admission (Kyverno `verifyImages` or Sigstore policy-controller) |
| Vulnerable dependencies or base image | Build | Multi-stage, slim runtime | Trivy or Grype gate, Dependabot, dependency review, SBOM (Syft), provenance attestation |
| Pipeline pushes bad config straight to prod | Git | Dev only | PR with review for prod, CODEOWNERS, protected branch, required status checks |
| Leaked registry credential | Cluster | Read-only scope, namespaced Secret, not in Git | Vault and ESO, rotation, robot account, alert on anomalies |
| Container breakout or privilege abuse | Runtime | Non-root user in image | `runAsNonRoot`, drop all capabilities, read-only root filesystem, seccomp `RuntimeDefault`, Pod Security Admission `restricted` on the namespace |
| Lateral movement in cluster | Network | STRICT mTLS | Default-deny NetworkPolicy plus Istio `AuthorizationPolicy` by service account |
| Secret exposure through Actuator | App | Only health, info, prometheus exposed | Secure the actuator port, separate management port, authentication |
| Data in transit | Edge | mTLS inside the mesh | TLS at the gateway, HSTS, modern ciphers |
| No evidence after an incident | All | Git history and Actions logs | Kubernetes audit logs, Istio access logs shipped centrally, retention policy |

### 10.2 Hardening snippets (to add later)

Pod Security on the namespace:

```powershell
kubectl label namespace demo pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/warn=restricted
```

Default-deny NetworkPolicy plus allow from the Istio ingress gateway namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: demo
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
```

Istio default-deny and a scoped allow:

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-ingress-gateway
  namespace: demo
spec:
  selector:
    matchLabels:
      app: demo
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"]
```

Image scan step in CI (add after the build step, before push, as a gate):

```yaml
      - name: Scan image
        uses: aquasecurity/trivy-action@<pin-to-commit-sha>
        with:
          image-ref: ${{ env.IMAGE }}:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: "1"
```

Branch protection for `main` (when the bot opens PRs instead of pushing): require pull request reviews, require the `ci` status check, restrict who can push, require signed commits if policy demands.

### 10.3 Security design principles (say these in an interview)

1. **Least privilege everywhere:** token scopes per job, read-only pull credentials, non-root containers, namespace boundaries.
2. **No long-lived secrets where identity can replace them:** `GITHUB_TOKEN`, OIDC, workload identity.
3. **Immutability:** SHA tags (better: digests), signed artifacts, GitOps-reconciled state.
4. **Separation of duties:** CI cannot deploy, developers cannot change production config without review.
5. **Defence in depth:** scan, sign, admit, isolate (network and mesh), observe.
6. **Everything auditable:** Git history, Actions logs, cluster audit logs.

---

## 11. Troubleshooting matrix (real and likely)

| Symptom | First command | Likely cause | Fix |
|---|---|---|---|
| Workflow does not start | Actions tab, `git ls-files .github` | `ci.yml` not in `.github/workflows/`, or `paths:` did not match | Fix location, include a file under `demo/**` |
| `Build and test` fails | Step log | Missing `pom.xml`, Java mismatch, failing test | Run `mvn -B verify` in `demo/` |
| `denied: permission_denied: write_package` | Step log | Workflow permissions read-only, or missing `packages: write` | Settings, Actions, General, Read and write |
| `invalid reference format` | Step log | Uppercase in image name | Keep `IMAGE` lowercase |
| `update-deploy` push rejected | Step log | Branch protection blocks the bot | Allow it, or switch to PR flow |
| `git push` rejected locally | `git status` | Bot commit not pulled | `git pull --rebase` |
| `ErrImagePull`, "repository does not exist" on docker.io | `describe pod` | Image name has no registry host, or local image missing on kind | Use the full GHCR name |
| `ImagePullBackOff`, `unauthorized` | `describe pod`, `kubectl get pod -o jsonpath="{.spec.imagePullSecrets}"` | Secret missing, wrong namespace, expired PAT, wrong scope | Recreate `ghcr-pull`, restart rollout |
| `manifest unknown` | `describe pod` | Tag not pushed (CI failed or tag typo) | Check the package page and `values-dev.yaml` |
| Pod `1/2` | `kubectl describe pod` | Sidecar up, app container failing | Read the app container events |
| Pod `1/1` | `kubectl get ns demo --show-labels` | Injection label missing or pod not restarted | Label, then `kubectl rollout restart` |
| `namespace/demo not labeled` | | Label already set with same value (not an error) | None |
| Gateway 404 | `Invoke-RestMethod` with header | Wrong or missing `Host` header | `-Headers @{Host="demo.local"}` |
| Gateway 503 | `kubectl get svc -n demo`, VirtualService host | Wrong Service name (`demo-demo` vs `demo`), or no Ready pods | Fix destination host, check endpoints |
| `kubectl patch` JSON error | | PowerShell strips quotes | Use YAML files and `kubectl apply` |
| Outsider call succeeds | `kubectl get peerauthentication -n demo` | Mode is PERMISSIVE | Set STRICT |
| OOMKilled | `describe pod` (Last State, exit 137) | Heap too close to limit | Lower `MaxRAMPercentage`, raise limit |
| Cluster lost | `kind get clusters` | kind node container deleted | Recreate cluster and Istio, reapply from Git (image comes from GHCR, no side-load) |

---

## 12. Operating notes

- **Token expiry:** a classic PAT can expire. When it does, running pods keep working; the next pod that must pull (new node, new tag) fails with `unauthorized`. Put the expiry date in your calendar, or use a longer-lived robot credential.
- **Cached images:** with `IfNotPresent`, never reuse a tag. The commit SHA guarantees a fresh pull.
- **Cost of CI:** `concurrency` and `paths:` limit runs; the Maven and Docker caches shorten them.
- **Rebuilding the lab:** the repo is the backup. Cluster loss costs about 15 minutes: recreate namespace and label, recreate `ghcr-pull`, `helm install`, apply `deploy/istio/`.
- **Keep Git and cluster aligned:** if you run `helm rollback` or `kubectl rollout undo`, record it with a Git revert, otherwise the next deploy silently undoes it.

---

## 13. Interview talking points from this page

| Question | Answer in one breath |
|---|---|
| Describe your CI/CD flow | "Push triggers tests and an image build tagged with the commit SHA, pushed to GHCR. A second job commits that SHA into the Helm values. CI never touches the cluster; deployment comes from Git." |
| Why not `helm upgrade` in the pipeline? | "That would put cluster credentials in CI and leave no reviewed record. Git as the source of truth gives audit, review and `git revert` rollback." |
| How do you avoid pipeline loops? | "`GITHUB_TOKEN` pushes do not trigger workflows, and the bot only changes `deploy/**`, which my `paths` filter ignores." |
| How is the registry secured? | "`GITHUB_TOKEN` for push, a read-only credential in a namespaced Secret for pull; in production Vault and External Secrets, and signed images verified at admission." |
| How do you prove zero downtime? | "A load generator inside the cluster during a rolling restart: 1550 requests, all 200, thanks to readiness gating, `maxUnavailable: 0`, `preStop` and graceful shutdown." |
| What would you change for production? | "Separate deployment repo with PRs, Argo CD with environments, image scanning and signing, Pod Security restricted, default-deny network and Istio authorization, HTTPS at the gateway, Vault for secrets." |
| What went wrong and what did you learn? | "A gateway 503 from a Service name mismatch, an ImagePullBackOff from a missing image, a CI failure specific to GHCR. Each time the status code or event message pointed at the layer to look at." |

---

## 14. Quick command reference

```powershell
# Git
git pull
git log --oneline -5
git tag block-3-done ; git push origin main --tags

# CI result
# https://github.com/pravatvmware/Spring-Boot-Platform-Lab/actions

# Helm
helm lint deploy/helm/demo
helm template demo deploy/helm/demo -f deploy/helm/demo/values-dev.yaml
helm upgrade demo deploy/helm/demo -n demo -f deploy/helm/demo/values-dev.yaml
helm history demo -n demo
helm get values demo -n demo

# Kubernetes
kubectl get deploy,rs,pods,svc,endpoints -n demo
kubectl describe pod -n demo -l app=demo
kubectl logs deploy/demo -n demo --previous
kubectl get events -n demo --sort-by=.lastTimestamp
kubectl rollout restart deploy/demo -n demo
kubectl rollout status deploy/demo -n demo

# Pull secret
kubectl get secret ghcr-pull -n demo
kubectl get secret ghcr-pull -n demo -o jsonpath="{.type}"

# Istio
istioctl proxy-status
istioctl analyze -n demo
kubectl logs -n istio-system deploy/istio-ingressgateway --tail=5
kubectl get peerauthentication -n demo
```

---

## 15. Self-check before moving to Block 4

- [ ] I can draw the flow from `git push` to a running pod and name every credential on the way
- [ ] I can explain why CI does not run `helm upgrade`
- [ ] I can explain the two jobs and why `update-deploy` depends on `build`
- [ ] I know what lives in Git, in the registry, and in the cluster Secret
- [ ] I can list five production hardening items not yet in the lab and why each matters
- [ ] I know which error message maps to which layer (404 vs 503, `unauthorized` vs `manifest unknown`)
- [ ] I have a screenshot of a green run with both jobs, and the bot commit, for my docs

## Next

[Block 4: Break things and fix them](04-break-and-fix). The first drill is the missing pull secret (`ImagePullBackOff` with `unauthorized`), where `maxUnavailable: 0` keeps the old pod serving.

{% endraw %}
