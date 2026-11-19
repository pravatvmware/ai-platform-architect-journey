---
layout: default
title: "Block 1: App, Actuator, Docker"
parent: 8. Spring Boot Platform Lab
nav_order: 4
---

# Block 1: App, Actuator, Docker

**Date:** 2026-11-10
**Code:** [block-1-done](https://github.com/pravatvmware/Spring-Boot-Platform-Lab/tree/block-1-done)

## Goal

Build a Spring Boot service that is operable by a platform team: health groups for Kubernetes probes, Prometheus metrics, graceful shutdown, and a small, non-root container image with container-aware JVM settings.

## Prerequisites

Docker Desktop, kind, Istio. Java and Maven are optional locally because the Docker build compiles the app.

```
<paste: docker version, java -version, mvn -v>
```

## Steps

### Step 1: Generate the project

start.spring.io: Maven, Java 21, dependencies Web, Actuator, Prometheus. Project lives in `demo/`.

### Step 2: Endpoint

`HelloController` returns `Hello from <HOSTNAME>`. In a container `HOSTNAME` is the container ID, in Kubernetes it is the pod name.

### Step 3: Actuator config (`application.yml`)

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

- `exposure.include` limits which endpoints are reachable. Exposing everything is a security risk.
- `probes.enabled` adds `/actuator/health/liveness` and `/actuator/health/readiness`.
- `server.shutdown: graceful` lets in-flight requests finish on SIGTERM.

### Step 4: Dockerfile (multi-stage, non-root)

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

## Verification

Container run on port 8085:

```
PS> Invoke-RestMethod -Uri http://localhost:8085/hello
Hello from demo app 395a9444539b
```

Add your own outputs here:

```
<paste: cached rebuild output (dependency layer CACHED)>
<paste: docker exec demo id  -> uid=1001>
<paste: MaxHeapSize with -m 512m (about 384 MB) and -m 1g>
<paste: docker images demo:1>
```

## What broke and how I fixed it

| Symptom | Cause | Fix |
|---|---|---|
| (add rows as they happen) | | |

## Key concepts (checkpoint answers)

**Endpoints.** `/actuator/health` is the overall status. `/liveness` answers "is the process stuck?" and drives the livenessProbe (restart). `/readiness` answers "can it serve traffic now?" and drives the readinessProbe (remove from Service endpoints). `/prometheus` exposes metrics in Prometheus text format. Liveness must not depend on the database, otherwise a DB outage restarts every pod.

**Multi-stage and `pom.xml` before `src`.** Stage 1 holds the JDK and Maven for compiling; stage 2 holds only the JRE and the JAR. The image is smaller, has fewer CVEs, and no build tools in production. Copying `pom.xml` first creates a cached dependency layer that is reused when only source code changes, so rebuilds take seconds.

**`MaxRAMPercentage` instead of `-Xmx`.** The JVM sizes the heap from the container memory limit, so the same image works with any limit. A fixed `-Xmx` either wastes memory or causes OOMKilled when the limit changes. Not 100%, because total memory is heap plus metaspace, thread stacks, direct buffers and JVM overhead.

**Non-root user.** Least privilege. A compromised app gets an unprivileged user, a container escape is less damaging, and policies (Pod Security `restricted`, Kyverno, OpenShift) require it. Use a numeric UID so `runAsNonRoot` can be verified.

**Graceful shutdown.** On SIGTERM Spring stops accepting new requests, lets in-flight ones finish (up to 30s), then exits. Without it, rollouts cut requests and users see 502/503. It works together with readiness probes, a short `preStop` sleep and a `terminationGracePeriodSeconds` larger than the drain time.

## How I would explain this in an interview

> "I built a Spring Boot service with Actuator health groups and Micrometer metrics, and containerized it with a multi-stage, non-root image and container-aware JVM settings. I verified that the heap scales with the container limit and that a rebuild after a source change reuses the cached dependency layer."

## Next

[Block 2: kind, Helm, Istio](02-kind-helm-istio)
