---
layout: default
title: Lab setup
parent: 8. Spring Boot Platform Lab
nav_order: 2
---

# Lab setup

## Environment

| Item | Value |
|---|---|
| OS | Windows, PowerShell |
| Container runtime | Docker Desktop |
| Kubernetes | kind cluster `enterprise-sandbox` (node `enterprise-sandbox-control-plane`) |
| Service mesh | Istio 1.30.3 (client, control plane, data plane) |
| Helm | v4.3.1 |
| Observability in `istio-system` | Prometheus, Grafana, Kiali, Alertmanager |
| Code repo | `pravatvmware/Spring-Boot-Platform-Lab`, branch `main` |
| Registry | GHCR (`ghcr.io/pravatvmware/spring-boot-platform-lab/demo`) |

The cluster also holds the Online Boutique images from an earlier lab. This project uses its own `demo` namespace so nothing collides.

## Repo layout

```
Spring-Boot-Platform-Lab/
  README.md
  .gitignore
  .github/workflows/ci.yml
  demo/                     Spring Boot project (pom.xml, Dockerfile, src)
  deploy/
    k8s/demo.yaml           plain manifests
    helm/demo/              Helm chart (values, values-dev, values-prod)
    istio/                  gateway.yaml, peer-authentication.yaml
```

## Pre-flight checks

{% raw %}
```powershell
docker version --format '{{.Server.Version}}'
kubectl config current-context
kubectl get nodes
istioctl version
helm version
kind get clusters
```
{% endraw %}

## Reaching things from Windows

The ingress gateway Service is `LoadBalancer` with `EXTERNAL-IP <pending>` because kind has no cloud load balancer. Use port-forward:

```powershell
kubectl port-forward -n istio-system svc/istio-ingressgateway 8088:80
Invoke-RestMethod -Uri http://localhost:8088/hello -Headers @{Host="demo.local"}
```

Kiali:

```powershell
kubectl port-forward -n istio-system svc/kiali 20001:20001
```

## Known quirks of this setup

- kind nodes cannot see Docker Desktop images. Use `kind load docker-image demo:1 --name enterprise-sandbox`, or pull from a registry.
- If `kind load` errors on newer Docker Desktop, use `docker save demo:1 -o demo.tar` then `kind load image-archive demo.tar --name enterprise-sandbox`.
- PowerShell strips inner double quotes when calling native programs. Prefer YAML files and `kubectl apply` over inline JSON patches.
- Istio injection needs a namespace label and a pod restart: `kubectl label namespace demo istio-injection=enabled`.
