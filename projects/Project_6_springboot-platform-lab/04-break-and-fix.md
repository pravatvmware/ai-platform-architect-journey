---
layout: default
title: "Block 4: Break things and fix them"
parent: 8. Spring Boot Platform Lab
nav_order: 7
---

# Block 4: Break things and fix them

**Status:** Not started

## Goal

Cause the common failures on purpose, diagnose each from symptoms, and record the evidence. Breaking things deliberately is how you get real troubleshooting stories.

## Drills

For each drill: cause it, observe, diagnose with commands, fix, record.

| # | Drill | How to cause it | Expected symptom | Diagnose with |
|---|---|---|---|---|
| 1 | OOMKilled | Set memory limit to 128Mi, redeploy | Pod restarts, exit code 137 | `kubectl describe pod` (Last State), `kubectl get pod` restarts |
| 2 | CrashLoopBackOff | Set a bad env var, for example a wrong datasource URL or bad profile name | Pod crashes at start | `kubectl logs --previous`, first `Caused by:` |
| 3 | Pod never Ready | Wrong readiness probe path | `0/2`, removed from Endpoints | `kubectl describe pod` (Unhealthy events), `kubectl get endpoints` |
| 4 | Liveness kills a slow starter | Remove startupProbe, tight liveness delay | Restarts during boot | Events, probe settings |
| 5 | Dropped requests on rollout | Remove `preStop`, graceful shutdown and set `maxUnavailable: 1`, run the load generator | Possible 502/503/000 in loadgen | Compare status code counts with the baseline (1550 x 200) |
| 6 | Image pull failure | Delete `ghcr-pull`, restart | `ErrImagePull`, `unauthorized` | `kubectl describe pod`; the old pod keeps serving because of `maxUnavailable: 0` |
| 7 | Gateway 503 | Point the VirtualService at a wrong host | 503 with a valid Host header | `istioctl analyze`, gateway access log flags |
| 8 | STRICT mTLS rejection | Call from a non-mesh pod | Connection reset | Compare PERMISSIVE and STRICT |

## Record for each drill

```
Symptom:
Commands used and what they showed:
Root cause:
Fix:
How to prevent it:
```

## Debug commands

```bash
kubectl logs deploy/demo --previous
kubectl describe pod <pod>
kubectl get events -n demo --sort-by=.lastTimestamp
kubectl top pod -n demo
kubectl debug -it <pod> --image=eclipse-temurin:21 --target=demo
istioctl analyze -n demo
istioctl proxy-status
```

## Results

Add a section per drill as you complete it, with real output.

## Next

[Block 5: Maven essentials](05-maven-essentials)
