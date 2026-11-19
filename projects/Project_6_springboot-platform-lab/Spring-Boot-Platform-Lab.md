---
layout: default
title: 8. Spring Boot Platform Lab
nav_order: 7
has_children: true
---

# Spring Boot Platform Lab

A hands-on DevOps / platform engineering project, built step by step and documented with real command output.

**Code repo:** [pravatvmware/Spring-Boot-Platform-Lab](https://github.com/pravatvmware/Spring-Boot-Platform-Lab)

## Goal

Practice the day-to-day workflow of a platform engineer supporting Java services:

- Build and containerize a Spring Boot service the right way
- Deploy it to Kubernetes (kind) with proper probes and graceful shutdown
- Package it with Helm and run it inside an Istio mesh
- Deliver it through GitHub Actions to a registry (GHCR), with the image tag committed to Git
- Break it on purpose and diagnose it, so the troubleshooting stories are real

## Architecture

```
developer push
     |
     v
GitHub Actions: mvn verify -> docker build -> push to GHCR (tag = git SHA)
     |
     v
update-deploy job: yq sets image.tag in values-dev.yaml -> commit to Git
     |
     v
helm upgrade (later: Argo CD syncs automatically)
     |
     v
kind cluster: Istio ingress gateway -> VirtualService -> demo pods (app + istio-proxy)
     |
     v
Prometheus / Grafana / Kiali (already in istio-system)
```

## Progress

| Block | Topic | Status |
|---|---|---|
| 1 | [App, Actuator, Docker](01-app-actuator-docker) | Done |
| 2 | [kind, Helm, Istio](02-kind-helm-istio) | Done (Kiali screenshot optional) |
| 3 | [GitHub Actions and GHCR](03-github-actions) | In progress (CI error to fix) |
| 4 | [Break things and fix them](04-break-and-fix) | Not started |
| 5 | [Maven essentials](05-maven-essentials) | Not started |
| 6 | [Interview Q&A](06-interview-qa) | Not started |

## Pages

- [Roadmap](roadmap): what is done, what is next, and ideas for extensions
- [Lab setup](lab-setup): tools, versions, and how to recreate the environment
- [Troubleshooting log](troubleshooting-log): every problem hit, with cause and fix
- [Commands cheat sheet](cheatsheet): the commands used most often
- [Page template](template): copy this for each new block

## Tech

Java 21, Spring Boot, Maven, Docker Desktop, kind, Istio 1.30, Helm 4, GitHub Actions, GHCR, Prometheus, Grafana, Kiali