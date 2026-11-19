---
layout: default
title: Roadmap
parent: 8. Spring Boot Platform Lab
nav_order: 1
---

# Roadmap

Last updated: 2026-11-19

## Status by block

| Block | What it builds | Status | Code tag |
|---|---|---|---|
| 1 | Spring Boot app, Actuator, Prometheus metrics, Docker image | Done | `block-1-done` |
| 2A | Plain Kubernetes manifests, probes, graceful shutdown | Done | |
| 2B | Helm chart with dev and prod values | Done | |
| 2C | Istio sidecar, Gateway, VirtualService, STRICT mTLS | Done | `block-2-done` |
| 3A | GitHub Actions: test, build, push to GHCR | Fix CI error, then verify | |
| 3B | CI updates image tag in Helm values, cluster pulls from GHCR with `imagePullSecrets` | Not started | |
| 4 | Break and fix drills | Not started | |
| 5 | Maven essentials | Not started | |
| 6 | Interview Q&A practice | Not started | |

## Next actions

1. Open the failing CI run, copy the log of the failing step into [the troubleshooting log](troubleshooting-log), fix, and push.
2. Finish Block 3B: values update job, pull secret, deploy from GHCR.
3. Block 4: break things on purpose (OOMKilled, CrashLoopBackOff, wrong probe path, missing pull secret).
4. Write each block page right after finishing it, while the output is fresh.

## Extension ideas

| Idea | Why it matters |
|---|---|
| Move Gateway and VirtualService into the Helm chart | Avoids name drift (the 503 issue); uses `demo.fullname` helper |
| Add Argo CD watching the deployment values | Replaces the manual `helm upgrade` step: the full GitOps loop |
| Separate deployment repo | Matches the app repo to deployment repo pattern used in real teams |
| ServiceMonitor plus a Grafana dashboard | Closes the loop from code to dashboard |
| External Secrets Operator with Vault | Production pattern for pull secrets and app secrets |
| Trivy image scan in CI | Supply chain security gate |
| Terraform to create the kind cluster and namespaces | Covers the IaC part of the role |

## Definition of done for a block

- Code committed and tagged
- Page written with real output
- Problems added to the troubleshooting log
- Progress table updated here and on the home page
