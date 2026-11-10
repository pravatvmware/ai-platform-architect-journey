---
layout: default
title: 8. Spring Boot Platform Lab
nav_order: 7
has_children: true
---

# Spring Boot Platform Lab

An end-to-end, hands-on project: a Spring Boot service built, containerized,
deployed to Kubernetes (kind) inside an Istio mesh, delivered with Helm and
GitHub Actions, observed with Prometheus, and deliberately broken and fixed.

**Goal:** practice the DevOps/platform engineer workflow for Java services
and document every step with real evidence.

## Architecture

![architecture](images/architecture.png)

Code → GitHub Actions (build, test, image) → registry → Helm values
→ kind cluster (Istio sidecar, Gateway) → Prometheus/Grafana

## Progress

| Block | Topic | Status |
|---|---|---|
| 1 | [App, Actuator, Docker](01-app-actuator-docker) | In progress |
| 2 | [kind, Helm, Istio](02-kind-helm-istio) | Not started |
| 3 | [GitHub Actions](03-github-actions) | Not started |
| 4 | [Break and fix](04-break-and-fix) | Not started |
| 5 | [Maven essentials](05-maven-essentials) | Not started |
| 6 | [Interview Q&A](06-interview-qa) | Not started |

## Tech

Java 21 · Spring Boot · Maven · Docker · kind · Istio · Helm ·
GitHub Actions · Prometheus · Grafana

five claims: read, debug, containerize, Actuator, Maven pipelines.

