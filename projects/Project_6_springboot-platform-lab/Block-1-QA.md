---
layout: default
title: Block 1: App, Actuator, Docker Q/A
parent: 8. Spring Boot Platform Lab
nav_order: 3
---

Block 1 Checkpoint: Answers

Read these, then say each one back in your own words. That’s what makes them stick for the interview.

Q0. What do health, liveness, readiness, and prometheus give you?
Endpoint	What it returns	Who uses it
/actuator/health	Overall status (UP/DOWN), optionally with details for DB, disk, and other dependencies	Humans, load balancers, simple monitors
/actuator/health/liveness	“Is the process alive, or stuck beyond recovery?”	Kubernetes livenessProbe (restart the container if it fails)
/actuator/health/readiness	“Can this instance serve traffic right now?”	Kubernetes readinessProbe (remove the pod from Service endpoints if it fails)
/actuator/prometheus	Metrics in Prometheus text format (JVM memory, GC, threads, HTTP request counts and latency, Hikari pool)	Prometheus scrapes it, Grafana graphs it, Alertmanager alerts on it

Key distinction: liveness failing means restart me, readiness failing means stop sending me traffic, but don’t kill me. Liveness should stay lightweight and never depend on the database, otherwise a DB outage restarts every pod and makes things worse.

Interview line: “Health groups drive Kubernetes probes, and the Prometheus endpoint feeds monitoring, so the app is both self-reporting and observable.”

Q1. Why is the build multi-stage, and why is pom.xml copied before src?

Multi-stage:

Stage 1 has the full JDK and Maven, which are needed only to compile.
Stage 2 copies just the final JAR onto a small JRE image.
Result: a smaller image, a smaller attack surface (no compilers or build tools in production), faster pulls and startup, and fewer CVEs to scan.

pom.xml before src:

Docker caches each layer, and a layer is rebuilt only if its inputs changed (or an earlier layer changed).
Dependencies change rarely, source code changes constantly.
Copying pom.xml first and running dependency:go-offline creates a cached “dependencies” layer. When you edit only source code, that layer is reused and only the compile step reruns.
Result: rebuilds drop from minutes to seconds, which also speeds up CI.

You saw this when the rebuild printed CACHED for the dependency layer.

Q2. Why MaxRAMPercentage instead of a fixed -Xmx?
A fixed -Xmx384m is baked into the image. If Kubernetes later gives the pod 1 GiB or 256 MiB, the heap doesn’t adapt. It wastes memory in the first case and gets the pod OOMKilled in the second.
MaxRAMPercentage=75 makes the JVM read the container’s memory limit (cgroups) and size the heap as a percentage of it. The same image works in dev (small limit) and prod (bigger limit) with no rebuild.
You verified it: 512 MB limit gave a heap of roughly 384 MB, and 1 GB scaled up.
Why not 100%? Total JVM memory is heap + metaspace + thread stacks + direct buffers + JVM overhead. If the heap takes everything, the kernel kills the container with exit code 137. In practice use about 60 to 75%.

Interview line: “I size the heap relative to the container limit so the same image is portable across environments and leaves headroom for non-heap memory.”

Q3. Why a non-root user?
Least privilege: if the app is compromised (a deserialization bug, say), the attacker gets an unprivileged user, not root inside the container.
It limits the damage of a container escape, since a root process in the container is root-equivalent on the kernel boundary.
It is required by policy in most real platforms: Kubernetes Pod Security Standards (restricted), OPA/Kyverno policies, and OpenShift all reject or flag root containers.
It enables hardening such as runAsNonRoot: true, readOnlyRootFilesystem, and dropping Linux capabilities.

You verified it with docker exec demo id showing uid=1001.

One practical note: a numeric UID (USER 1001) is better than a name, because Kubernetes’ runAsNonRoot check can verify a number but can’t resolve a name.

Q4. What does server.shutdown: graceful prevent?

During a rollout, Kubernetes sends SIGTERM to the old pod. Without graceful shutdown, Spring stops the web server immediately and:

in-flight requests are cut off, so users see 502/503 or connection resets,
long-running requests and half-finished work are lost.

With graceful, the app:

stops accepting new requests,
lets in-flight requests finish, up to timeout-per-shutdown-phase (30s here),
then exits cleanly.

It works best together with:

a readiness probe, so the pod is removed from the Service endpoints,
a short preStop sleep (a few seconds), because endpoint removal takes a moment to propagate,
terminationGracePeriodSeconds greater than the shutdown timeout (for example 45s), otherwise Kubernetes SIGKILLs the pod mid-drain.

We’ll test this in Block 2 and Block 4.

One-minute summary to say out loud

“The app exposes Actuator health groups so Kubernetes can restart stuck pods via liveness and hold traffic back via readiness, plus a Prometheus endpoint for metrics. The image is built multi-stage with the dependency layer cached, so it’s small, fast to rebuild, and has no build tools in production. The JVM heap is a percentage of the container limit so it adapts to the environment, the process runs as a non-root user for least privilege, and graceful shutdown means rollouts don’t drop in-flight requests.”