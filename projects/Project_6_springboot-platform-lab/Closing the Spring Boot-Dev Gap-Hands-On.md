---
layout: default
title: Phase 1 - Closing the Spring Boot / Dev Gap (Hands-On)
parent: 8. Spring Boot Platform Lab
nav_order: 1
---

five claims: read, debug, containerize, Actuator, Maven pipelines.

Closing the Spring Boot / Dev Gap (Hands-On)

Your sentence makes five claims: read, debug, containerize, Actuator, Maven pipelines. The goal is to make each one something you’ve done this week, so you can say “I built a sample to match your stack” and answer follow-ups from experience. A platform engineer isn’t expected to write features fast. They’re expected to run, debug, ship, and observe Java services, and that’s what this plan covers.

Plan on about 4 to 6 hours of hands-on work across a day or two.

1. Minimum Java/Spring Boot Knowledge (read in 30 min)
Concept	What to know
Project layout	pom.xml, src/main/java, src/main/resources/application.yml, src/test
Annotations	@SpringBootApplication, @RestController, @GetMapping, @Service, @Value, @ConfigurationProperties, @Profile
Config order	Env vars override application.yml, and SPRING_PROFILES_ACTIVE=prod loads application-prod.yml. Env var SPRING_DATASOURCE_URL maps to spring.datasource.url
Fat JAR	mvn package produces one runnable JAR with an embedded Tomcat, run with java -jar
Starters	spring-boot-starter-web, -actuator, -data-jpa, -security, -oauth2-resource-server
Datasource	HikariCP connection pool. Pool exhaustion is a classic production issue
Logging	Logback, levels via logging.level.root=INFO, structured JSON logs for ELK/Loki

You don’t need to write complex business logic. Be able to open a controller, follow a request to the DB call, and read a stack trace.

2. Hands-On Lab (build this once)
Step 1: A tiny app with Actuator and Prometheus metrics

Generate a project at start.spring.io (Maven, Java 17 or 21) with dependencies: Spring Web, Actuator, Prometheus.

java
@RestController
class HelloController {
    @GetMapping("/hello")
    String hello() { return "Hello from " + System.getenv().getOrDefault("HOSTNAME","local"); }
}

application.yml:

yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  endpoint:
    health:
      probes:
        enabled: true          # adds /actuator/health/liveness and /readiness
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s

Run mvn spring-boot:run, then check:

curl localhost:8080/actuator/health
curl localhost:8080/actuator/health/readiness
curl localhost:8080/actuator/prometheus | head

You can now say: “I expose health groups for Kubernetes probes and Micrometer metrics for Prometheus.”

Step 2: Containerize it (multi-stage, non-root, container-aware JVM)
dockerfile
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B -q dependency:go-offline        # caches dependencies in a layer
COPY src ./src
RUN mvn -B package -DskipTests

FROM eclipse-temurin:21-jre
RUN useradd -r -u 1001 app
USER 1001
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-XX:MaxRAMPercentage=75","-jar","app.jar"]

Build and run: docker build -t demo:1 . && docker run -p 8080:8080 -m 512m demo:1

Know why: a multi-stage build keeps the Maven and JDK out of the runtime image. The dependency layer is cached when only source changes. A non-root user limits blast radius. MaxRAMPercentage makes the heap respect the container’s memory limit.

Step 3: Deploy to Kubernetes with proper probes

Use kind or minikube locally.

yaml
containers:
- name: app
  image: demo:1
  ports: [{containerPort: 8080}]
  env:
  - {name: SPRING_PROFILES_ACTIVE, value: dev}
  resources:
    requests: {cpu: 250m, memory: 512Mi}
    limits:   {memory: 768Mi}
  startupProbe:
    httpGet: {path: /actuator/health/liveness, port: 8080}
    failureThreshold: 30
    periodSeconds: 5
  readinessProbe:
    httpGet: {path: /actuator/health/readiness, port: 8080}
    periodSeconds: 10
  livenessProbe:
    httpGet: {path: /actuator/health/liveness, port: 8080}
    periodSeconds: 10

Wrap it as a Helm chart (helm create demo), parameterizing image, env, resources, and probes. Then optionally point an Argo CD Application at it.

Step 4: GitHub Actions pipeline (also closes your GitHub Actions gap)
yaml
name: ci
on:
  push: {branches: [main]}
  pull_request:
permissions:
  contents: read
  packages: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: {distribution: temurin, java-version: 21, cache: maven}
      - run: mvn -B -ntp verify
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

Later, swap ghcr.io for Artifactory and add a step that updates the image tag in the deployment repo with yq. That completes your GitOps story.

Step 5 (optional): Scrape the metrics

Install kube-prometheus-stack with Helm, add a ServiceMonitor pointing at /actuator/prometheus, and build one Grafana panel (request rate and JVM heap). The panel shows you can close the loop from code to dashboard.

3. Maven Essentials (30 min)
Topic	Know this
Lifecycle	validate → compile → test → package → verify → install → deploy
verify vs package	verify also runs integration tests and quality checks
Dependency problems	mvn dependency:tree finds conflicts, and -U forces snapshot update
SNAPSHOT vs release	SNAPSHOTs are mutable and for development. Releases are immutable. Use releases for deployable artifacts
settings.xml	Holds the mirror (point to Artifactory), server credentials (inject from CI secrets), and profiles
mvn deploy	Publishes the artifact to Artifactory (via distributionManagement)
CI flags	-B (batch), -ntp (no transfer progress), -DskipTests only in the image stage
Reproducibility	Pinned plugin and dependency versions, parent POM or BOM for consistency

Artifactory mirror in settings.xml:

xml
<mirror>
  <id>artifactory</id>
  <mirrorOf>*</mirrorOf>
  <url>https://artifactory.company.com/artifactory/maven-virtual</url>
</mirror>
4. Real DevOps Situations With Java Services

These are the situations interviewers use to test whether you can support developers. Be able to explain each one.

#	Situation	Likely cause	How you diagnose	Fix
1	Pod OOMKilled (exit 137)	Heap plus metaspace plus threads exceed the container limit, or heap fixed too high	kubectl describe pod (Last State), check MaxRAMPercentage, Grafana JVM heap/GC panels	Set MaxRAMPercentage=60-75, raise the limit with headroom, find leaks with a heap dump
2	Pod not Ready after deploy	Slow startup, probe too aggressive, or the DB is unreachable (readiness depends on it)	kubectl describe, /actuator/health output, logs	Add a startupProbe, tune delays, fix the dependency
3	CrashLoopBackOff right at startup	Missing env var or secret, wrong profile, bad DB URL, port conflict	kubectl logs --previous, read the first Caused by: line	Fix ConfigMap/Secret, check SPRING_PROFILES_ACTIVE
4	Slow or timing-out requests	Hikari pool exhausted, slow SQL, thread starvation	Metrics hikaricp_connections_active/pending, thread dump	Tune the pool, fix the query or index, scale replicas
5	High CPU / throttling	CPU limit too low, GC thrash, runaway loop	kubectl top, container throttling metric, thread dump	Raise or remove the CPU limit, tune the heap
6	Errors during rollout (brief 502/503)	No graceful shutdown or no readiness gating	Check server.shutdown=graceful, preStop sleep, PDB, rolling-update settings	Graceful shutdown plus terminationGracePeriodSeconds greater than the shutdown timeout
7	Build fails in CI, works locally	JDK version mismatch, missing dependency in the mirror, unavailable private repo credentials, flaky tests	Compare Java versions, read the Maven error, -X for debug	Pin the JDK in setup-java, fix settings.xml and secrets
8	ClassNotFound / NoSuchMethodError	Dependency version conflict	mvn dependency:tree -Dverbose	Align versions via BOM or dependencyManagement
9	JWT 401 after Keycloak integration	iss mismatch (internal vs external URL), wrong audience, JWKS unreachable, clock skew	Decode the token (jwt.io), compare against issuer-uri, test the JWKS URL from the pod	Align the issuer URL, fix the network or DNS, fix NTP
10	Kafka consumer lag rising	Slow processing, rebalances, too few partitions or consumers	Consumer-group describe, lag metrics, app logs	Scale consumers (up to the partition count), fix slow handlers, tune max.poll settings
11	Config change didn’t apply	ConfigMap updated but pod not restarted, or env var overrides the file	Check mounted values, /actuator/env (secured!)	Restart via a checksum annotation in the Helm chart or Reloader
12	Same image behaves differently across envs	Different profiles, config, or secrets	Diff the Helm values per environment	Keep the image identical and vary only config
Debugging commands to memorize
bash
kubectl logs deploy/app --previous
kubectl describe pod <pod>                       # events, exit code, OOMKilled
kubectl exec -it <pod> -- jcmd 1 Thread.print    # thread dump (needs a JDK image)
kubectl exec -it <pod> -- jcmd 1 GC.heap_info
kubectl debug -it <pod> --image=eclipse-temurin:21 --target=app   # when the image has no tools
kubectl top pod

Say: “If the runtime image is a JRE or distroless, I use an ephemeral debug container instead of fattening the production image.”

Reading a stack trace (practice for 10 minutes)
Read bottom-up for the root cause: find the last Caused by:.
Find the first line with your package name (com.company...), because that’s where your code is involved.
Common patterns: Connection refused (network/DB), UnsatisfiedDependencyException (bean wiring or missing config), Port already in use, OutOfMemoryError (heap, metaspace, or “unable to create native thread”).