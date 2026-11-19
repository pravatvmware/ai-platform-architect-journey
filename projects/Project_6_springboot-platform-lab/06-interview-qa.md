---
layout: default
title: "Block 6: Interview Q&A"
parent: 8. Spring Boot Platform Lab
nav_order: 9
---

# Block 6: Interview Q&A

Answers use the real work in this lab. Say them out loud.

## Java services on Kubernetes

**A Spring Boot pod keeps restarting. Walk me through it.**
`kubectl describe pod` for exit code and events (137 is OOM, 1 is an application failure), `kubectl logs --previous` and find the first `Caused by:`, then check config and secrets, probe settings and resource limits. If a liveness probe kills a slow starter, add a startup probe. Fix the cause, not the symptom.

**Why does a Java app get OOMKilled when the heap looks fine?**
Memory is heap plus metaspace, thread stacks, direct buffers and JVM overhead. Use `MaxRAMPercentage` around 60 to 75 percent and leave headroom.

**Should the liveness probe check the database?**
No. A DB outage would restart every pod. Liveness asks whether the process is stuck, readiness asks whether it can serve traffic.

**How do you make rollouts zero-downtime?**
Readiness probes, `maxUnavailable: 0`, graceful shutdown, a short `preStop` sleep, `terminationGracePeriodSeconds` longer than the drain, a PDB and multiple replicas. In this lab: 1550 requests, all 200, across a rolling restart.

## Helm and GitOps

**How do you manage environments with Helm?**
One chart, a defaults file and per-environment values files. CI changes only the image tag.

**Helm rollback vs Argo CD rollback?**
Helm rollback is imperative and leaves Git behind. In GitOps you revert in Git and the controller reconciles, keeping Git as the source of truth.

**Describe your pipeline.**
Push, test, build, push image tagged with the commit SHA, pipeline commits the SHA into the deployment values, a GitOps controller deploys. CI never needs cluster credentials.

## Istio

**What does sidecar injection do?**
A mutating webhook adds the Envoy proxy at pod creation, so pods must restart after labelling the namespace.

**What does STRICT mTLS do, and how did you prove it?**
It requires mesh certificates for inbound traffic. A pod outside the mesh was reset in STRICT mode and succeeded in PERMISSIVE mode.

**What does Istio do to probes?**
It rewrites them to go through the sidecar agent so kubelet checks work under strict mTLS.

**404 vs 503 at the gateway?**
404 means no route matched. 503 means the route matched but no healthy upstream was available; I found a wrong Service name in the VirtualService.

## Registry and secrets

**How does Kubernetes pull from a private registry?**
The kubelet authenticates with a `dockerconfigjson` Secret referenced by `imagePullSecrets`, on the pod or the ServiceAccount. Cloud platforms can use node identity instead.

**A pod works on one node and fails on another with ErrImagePull.**
The image is cached on the first node, so no auth is needed there; the second node must pull and fails on credentials.

**Manage pull secrets across many namespaces?**
Store the credential in Vault, sync it per namespace with External Secrets or a Kyverno generate policy, and use scoped, rotating robot credentials.

## Troubleshooting stories from this lab

| Story | Short version |
|---|---|
| `ErrImagePull` on kind | Image existed in Docker Desktop but not in the kind node; `kind load docker-image`. Lesson: in real setups the registry provides the image |
| Gateway 503 | Helm named the Service `demo`, VirtualService pointed to `demo-demo`. Lesson: read generated names or template them from the same helper |
| PowerShell patch error | Inner quotes stripped, kubectl got invalid JSON. Lesson: prefer declarative YAML |

## Platform scenarios to practice

- Secrets across cloud and hybrid environments (Vault, External Secrets, workload identity, OIDC from CI)
- Multi-tenancy in Kubernetes (namespaces, quotas, NetworkPolicies, AppProjects)
- Terraform state, modules and drift
- Observability: what to alert on (error rate, latency, saturation) and alert fatigue
