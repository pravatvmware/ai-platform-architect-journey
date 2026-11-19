---
layout: default
title: Troubleshooting log
parent: 8. Spring Boot Platform Lab
nav_order: 10
---

# Troubleshooting log

Every problem hit in the lab: symptom, diagnosis, cause, fix, lesson. Newest at the bottom.

## 2026-11-10: ErrImagePull on kind

- **Symptom:** pods in `ErrImagePull`, then `ImagePullBackOff`
- **Diagnosis:** `kubectl describe pod` showed a pull attempt against docker.io for `demo:1`
- **Root cause:** the image existed in Docker Desktop but not in the kind node's image store
- **Fix:** `kind load docker-image demo:1 --name enterprise-sandbox`, verified with `docker exec enterprise-sandbox-control-plane crictl images`, then `kubectl rollout restart deploy/demo -n demo`
- **Lesson:** kind nodes are separate containers. In real environments the image comes from a registry, which is what Block 3 provides. Read the event message: "repository does not exist on docker.io" means no registry in the image name, "unauthorized" means a credentials problem.

## 2026-11-10: 503 from the Istio ingress gateway

- **Symptom:** 503 through the gateway with a correct `Host: demo.local` header
- **Diagnosis:** a wrong Host would give 404, so the route matched and the upstream was the problem. Compared `kubectl get svc -n demo` with the VirtualService destination host
- **Root cause:** the VirtualService pointed to `demo-demo.demo.svc.cluster.local`, but the Helm name helper produced `demo` (the release name already contains the chart name)
- **Fix:** changed the destination host to `demo.demo.svc.cluster.local` and reapplied
- **Lesson:** 404 means no route matched, 503 means route matched but upstream unavailable. Do not guess Helm-generated names; read them from `kubectl get svc` or render them with `helm template`, or template the VirtualService from the same helper.

## 2026-11-10: kubectl patch JSON rejected in PowerShell

- **Symptom:** `error decoding patch: invalid character 's' looking for beginning of object key string`
- **Root cause:** Windows PowerShell strips inner double quotes when passing arguments to native programs, so kubectl received invalid JSON
- **Fix:** edit the YAML and `kubectl apply -f` (used), or escape the quotes, or use `--patch-file`
- **Lesson:** prefer declarative YAML over inline JSON patches: no quoting problems and Git stays the source of truth.

## 2026-11-10: First CI run failed

- **Symptom:** (paste the failing step name and error text)
- **Diagnosis:**
- **Root cause:**
- **Fix:**
- **Lesson:**

## Template for new entries

```
## YYYY-MM-DD: short title
- Symptom:
- Diagnosis (commands and what they showed):
- Root cause:
- Fix:
- Lesson / how to prevent:
```
