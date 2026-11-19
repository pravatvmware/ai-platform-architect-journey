---
layout: default
title: "Block 2: kind, Helm, Istio"
parent: 8. Spring Boot Platform Lab
nav_order: 5
---

# Block 2: kind, Helm, Istio

**Date:** 2026-11-10
**Code:** [block-2-done](https://github.com/pravatvmware/Spring-Boot-Platform-Lab/tree/block-2-done)

## Goal

Run the service on Kubernetes the way a platform team would: correct probes, zero-downtime rollouts, a reusable Helm chart, and traffic through an Istio gateway with STRICT mTLS.

---

## Part A: Plain manifests

Manifest: `deploy/k8s/demo.yaml` (Namespace, Deployment with 2 replicas, Service).

Key settings and why:

| Setting | Why |
|---|---|
| `maxUnavailable: 0`, `maxSurge: 1` | A new pod must be Ready before an old one is removed, so capacity never drops |
| `startupProbe` (30 x 5s) | Gives the JVM up to 150s to boot without being killed |
| `readinessProbe` | Keeps traffic away from pods that are not ready |
| `livenessProbe` | Restarts a stuck process |
| memory request 512Mi, limit 768Mi, `MaxRAMPercentage=75` | Heap about 576 MB, about 190 MB left for non-heap |
| `preStop: sleep 5` | Lets endpoint removal propagate before SIGTERM |
| `terminationGracePeriodSeconds: 45` | Covers preStop (5s) plus Spring drain (30s) with margin |

### Result after fixing the image load

```
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/demo   2/2     2            2           12m

replicaset.apps/demo-75455b9665   0   0   0   12m     (old, from the failed pull)
replicaset.apps/demo-86b895d969   2   2   2   5m30s

pod/demo-86b895d969-j7dtz   1/1   Running   0   5m23s
pod/demo-86b895d969-rsfbf   1/1   Running   0   5m30s

service/demo   ClusterIP   10.96.161.71   <none>   80/TCP

endpoints/demo   10.244.0.28:8080,10.244.0.29:8080
```

Notes: the Endpoints list is exactly the set of Ready pods. The old ReplicaSet stays at 0 for rollback history. The 7-second gap between pod ages shows the rolling update waiting for readiness.

### Load balancing from inside the cluster

```
Hello from demo-86b895d969-rsfbf
Hello from demo-86b895d969-j7dtz
Hello from demo-86b895d969-rsfbf
Hello from demo-86b895d969-j7dtz
Hello from demo-86b895d969-j7dtz
Hello from demo-86b895d969-j7dtz
```

`kubectl port-forward` pins to a single pod, so it does not show balancing.

### Rollout test

A load generator inside the cluster called the Service every 0.3s while `kubectl rollout restart` ran:

```
Name Count
---- -----
200   1550
```

All 1550 requests returned 200 during the test period, which included a full rolling restart.

---

## Part B: Helm chart

Chart in `deploy/helm/demo` with `values.yaml` (defaults), `values-dev.yaml` (1 replica) and `values-prod.yaml` (3 replicas, bigger memory).

Validation before install:

```
helm lint .
==> Linting .
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

Lifecycle test:

```
helm history demo -n demo
REVISION  STATUS      CHART       DESCRIPTION
1         superseded  demo-0.1.0  Install complete
2         superseded  demo-0.1.0  Upgrade complete
3         deployed    demo-0.1.0  Rollback to 1
```

Rollback creates a new revision (3) with the content of revision 1; it does not rewind the counter. The pod count returned to 1, matching `values-dev.yaml`.

Checkpoint answers:

1. `lint` checks structure and syntax; `template` renders the final YAML locally. Both are cheap CI gates before touching the cluster.
2. `values.yaml` holds defaults, `-f` files override it, `--set` overrides both. Maps merge by key, lists are replaced whole.
3. Chart `version` is the chart package version; `appVersion` describes the application being deployed. They change independently.
4. `helm rollback` is imperative and leaves Git out of date. In GitOps you `git revert` and the controller reconciles, so Git stays the source of truth.
5. The image tag is a value so one chart serves every environment, and CI only changes the tag.

---

## Part C: Istio

Cluster: Istio 1.30.3. The ingress gateway Service is `LoadBalancer` with `<pending>` (kind has no cloud load balancer), so it is reached by port-forward.

Injection: `kubectl label namespace demo istio-injection=enabled`, then `kubectl rollout restart deploy/demo -n demo`.

```
NAME                    READY   STATUS    RESTARTS   AGE
demo-7fcfff4678-sklt9   2/2     Running   0          37m
```

`2/2` means the app container plus `istio-proxy`.

Routing: `deploy/istio/gateway.yaml` defines a Gateway and a VirtualService for host `demo.local`.

```
PS> Invoke-RestMethod -Uri http://localhost:8088/hello -Headers @{Host="demo.local"}
Hello from demo-7fcfff4678-sklt9
```

A missing or wrong `Host` header gives 404 (no route matched). A 503 means the route matched but the upstream was unavailable. See the [503 entry in the troubleshooting log](troubleshooting-log).

### STRICT vs PERMISSIVE mTLS

An outsider pod (namespace without injection) called the service:

| Mode | Result |
|---|---|
| PERMISSIVE | `HTTP/1.1 200 OK`, `Hello from demo-7fcfff4678-sklt9` |
| STRICT | `Recv failure: Connection reset by peer` |

In STRICT mode the connection is established but the destination sidecar resets it because plain HTTP has no mesh certificate. The app never sees the request, so enforcement happens at the proxy.

Optional evidence to add:

```
<paste: probe rewrite output (kubectl get pod -o yaml | Select-String readinessProbe -Context 0,6)>
<paste: istioctl proxy-status | Select-String "demo|ingressgateway">
<screenshot: Kiali graph for namespace demo, saved as images/kiali-demo.png>
```

Checkpoint answers:

1. Injection adds the `istio-proxy` container through a mutating webhook at pod creation, so existing pods must be restarted.
2. `1/1` becomes `2/2` because the pod now has two containers.
3. The Gateway opens the port and host on the ingress proxy; the VirtualService defines where matching traffic goes.
4. The `Host` header selects the route; without a match the gateway returns 404.
5. `<pending>` because no load balancer exists on kind; use port-forward, MetalLB, or port mappings in the kind config.
6. Istio rewrites probes to go through the sidecar agent (port 15020) so kubelet checks keep working under strict mTLS.

## How I would explain this in an interview

> "I ran the service with proper probes and graceful shutdown and proved it with 1550 requests and zero failures across a rolling restart. I packaged it as a Helm chart with per-environment values, tested upgrade and rollback, then put it in an Istio mesh with a gateway and STRICT mTLS, and proved enforcement by showing a non-mesh pod was reset while the same call worked in PERMISSIVE mode."

## Next

[Block 3: GitHub Actions and GHCR](03-github-actions)
