---
layout: default
title: Block 1: App, Actuator, Docker
parent: 8. Spring Boot Platform Lab
nav_order: 2
---

Block 1: App, Actuator, Docker (about 45 min)
Step 0: Pre-flight check

Run these and note what each prints:

bash
docker version --format '{{.Server.Version}}'
kubectl get nodes
istioctl version
java -version
mvn -v
The first three should work, since you have Docker Desktop, kind, and Istio.
Java and Maven are optional. If java -version fails, skip Step 4 below. The Docker build in Step 5 compiles the app for you, which is the more important skill anyway.
Step 1: Generate the project

Use https://start.spring.io in a browser with these settings:

Project: Maven, Language: Java, Packaging: Jar, Java: 21
Group: com.example, Artifact: demo
Dependencies: Spring Web, Spring Boot Actuator, Prometheus

Click Generate, unzip it, and open a terminal in the demo folder.

Or from a terminal (Git Bash, macOS, or Linux):

bash
curl https://start.spring.io/starter.zip \
  -d type=maven-project -d javaVersion=21 \
  -d groupId=com.example -d artifactId=demo -d name=demo \
  -d dependencies=web,actuator,prometheus -o demo.zip
unzip demo.zip -d demo && cd demo

Look at the layout:

demo/
├── pom.xml                      # build + dependencies
├── mvnw, mvnw.cmd               # Maven wrapper (pins the Maven version)
└── src/main/
    ├── java/com/example/demo/DemoApplication.java
    └── resources/application.properties

Understand: pom.xml lists your starters. Open it and find spring-boot-starter-web, spring-boot-starter-actuator, and the Micrometer Prometheus registry. Each one gives a capability: HTTP server, health/metrics endpoints, and the Prometheus format.

Step 2: Add an endpoint

Create src/main/java/com/example/demo/HelloController.java:

java
package com.example.demo;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Hello from " + System.getenv().getOrDefault("HOSTNAME", "local");
    }
}

HOSTNAME is the pod name in Kubernetes, so later you can see load balancing across replicas.

Step 3: Configure Actuator

Delete application.properties and create src/main/resources/application.yml:

yaml
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

Understand each block:

exposure.include sets which Actuator endpoints are reachable over HTTP. Exposing everything (*) in production is a security risk.
probes.enabled adds /actuator/health/liveness and /actuator/health/readiness, which are what Kubernetes probes will call.
server.shutdown: graceful lets in-flight requests finish on SIGTERM. This prevents errors during rollouts.
Step 4: Run it locally (skip if no Java)
bash
./mvnw spring-boot:run        # Windows: mvnw.cmd spring-boot:run

In another terminal:

bash
curl localhost:8080/hello
curl localhost:8080/actuator/health
curl localhost:8080/actuator/health/liveness
curl localhost:8080/actuator/health/readiness
curl localhost:8080/actuator/prometheus | head -20

Expected: {"status":"UP"} for the health endpoints, and Prometheus-format text (jvm_memory_used_bytes, http_server_requests_seconds...) from the last call. Stop the app with Ctrl+C and watch the log say it is shutting down gracefully.

Step 5: Containerize it

Create Dockerfile in the project root (next to pom.xml):

dockerfile
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

Create .dockerignore:

target
.git

Build and run, with a 512 MB memory limit:

bash
docker build -t demo:1 .
docker run -d --name demo -p 8080:8080 -m 512m demo:1
curl localhost:8080/hello

Now rebuild after a tiny source change (edit the greeting) and watch the output. The dependency:go-offline layer should say CACHED, so the rebuild takes seconds. That is the layer caching you’ll explain in interviews.

Step 6: Verify the three things interviewers ask about

a) Container runs as non-root:

bash
docker exec demo id

Expected: uid=1001, not 0.

b) The JVM respects the container memory limit:

bash
docker run --rm -m 512m --entrypoint java demo:1 \
  -XX:MaxRAMPercentage=75 -XX:+PrintFlagsFinal -version | grep MaxHeapSize

(On PowerShell, replace | grep MaxHeapSize with | Select-String MaxHeapSize.)

Expected: roughly 384 MB (75% of 512 MB). Try again with -m 1g and see it scale. This is the basis for the OOMKilled discussion.

c) Image size and layers:

bash
docker images demo:1
docker history demo:1

Compare it mentally to a single-stage image with the JDK and Maven (several hundred MB larger).

Clean up when done: docker rm -f demo

Block 1 checkpoint

You should be able to answer these without looking:

What does each of health, liveness, readiness, and prometheus give you?
Why is the build multi-stage, and why is pom.xml copied before src?
Why MaxRAMPercentage instead of a fixed -Xmx?
Why a non-root user?
What does server.shutdown: graceful prevent?

Interview line you’ve earned:

“I built a Spring Boot service with Actuator health groups and Micrometer metrics, and containerized it with a multi-stage, non-root image and container-aware JVM settings. I verified that the heap scales with the container limit.”