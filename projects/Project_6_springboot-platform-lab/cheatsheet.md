---
layout: default
title: cheat sheet
parent: 8. Spring Boot Platform Lab
nav_order: 3
---

# Commands cheat sheet

PowerShell notes: avoid inline JSON with double quotes (use YAML files), and use backticks for line continuation.

## Docker

```powershell
docker build -t demo:1 ./demo
docker run -d --name demo -p 8085:8080 -m 512m demo:1
docker exec demo id
docker images demo:1
docker history demo:1
```

## kind

```powershell
kind get clusters
kind load docker-image demo:1 --name enterprise-sandbox
docker exec enterprise-sandbox-control-plane crictl images
```

## Kubernetes

```powershell
kubectl get deploy,rs,pods,svc,endpoints -n demo
kubectl describe pod -n demo -l app=demo
kubectl logs deploy/demo -n demo --previous
kubectl rollout restart deploy/demo -n demo
kubectl rollout status deploy/demo -n demo
kubectl get events -n demo --sort-by=.lastTimestamp
kubectl port-forward -n demo svc/demo 8081:80
kubectl run curl -n demo --rm -it --image=curlimages/curl --restart=Never -- curl -s http://demo/hello
```

Zero-downtime test:

```powershell
kubectl run loadgen -n demo --image=curlimages/curl --restart=Never -- sh -c "while true; do curl -s -o /dev/null -w '%{http_code}\n' http://demo/hello; sleep 0.3; done"
kubectl rollout restart deploy/demo -n demo
kubectl logs loadgen -n demo | Group-Object | Select-Object Name, Count
kubectl delete pod loadgen -n demo
```

## Helm

```powershell
helm lint deploy/helm/demo
helm template demo deploy/helm/demo -f deploy/helm/demo/values-dev.yaml
helm install demo deploy/helm/demo -n demo -f deploy/helm/demo/values-dev.yaml
helm upgrade demo deploy/helm/demo -n demo -f deploy/helm/demo/values-prod.yaml
helm history demo -n demo
helm rollback demo 1 -n demo
helm get values demo -n demo
```

## Istio

```powershell
kubectl label namespace demo istio-injection=enabled --overwrite
istioctl proxy-status
istioctl analyze -n demo
istioctl proxy-config routes deploy/istio-ingressgateway -n istio-system
kubectl logs -n istio-system deploy/istio-ingressgateway --tail=5
kubectl port-forward -n istio-system svc/istio-ingressgateway 8088:80
Invoke-RestMethod http://localhost:8088/hello -Headers @{Host="demo.local"}
```

Gateway response flags: `NR` no route, `UH` no healthy upstream, `UF` upstream connection failure, `URX` retry limit.

## Git and tags

```powershell
git add -A
git commit -m "blockN: message"
git tag block-N-done
git push origin main --tags
```

## Registry pull secret

```powershell
$env:GHCR_PAT = Read-Host "Paste PAT"
kubectl create secret docker-registry ghcr-pull -n demo --docker-server=ghcr.io --docker-username=pravatvmware --docker-password=$env:GHCR_PAT
Remove-Item Env:GHCR_PAT
```
