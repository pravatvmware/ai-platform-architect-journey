---
layout: default
title: Block 2, Istio, Starting Point
parent: 8. Spring Boot Platform Lab
nav_order: 7
---

Your mesh is healthy and has everything we need.

What your output tells us
Istio 1.30.3 for client, control plane and data plane, so no version skew.
istio-ingressgateway exists and is Running. Its Service is LoadBalancer with EXTERNAL-IP <pending>. kind has no cloud load balancer, so it will stay pending forever. That’s normal, and it means we reach the gateway with port-forward (or the NodePort, which is only reachable if you mapped ports when creating the cluster, so don’t rely on it).
Prometheus, Grafana, Kiali, Alertmanager are already in istio-system. This helps a lot: once traffic flows through the sidecar, Kiali will draw your service graph and Prometheus will hold Istio metrics, so you get the observability part of the story almost free.
16 proxies in the data plane come from your earlier Online Boutique lab. Our demo namespace is separate, so nothing collides. Note that istiod-revision-tag-default exists, which means injection may be revision-tag based. We’ll check that in C1 so the namespace label is correct.
C1: Check how injection is configured
powershell
kubectl get ns --show-labels | Select-String "istio"
kubectl get mutatingwebhookconfigurations | Select-String istio

Send me this output, or just try the standard label below. If pods don’t get a sidecar, the label style is the reason, and we’ll fix it.

C2: Enable sidecar injection on demo
powershell
kubectl label namespace demo istio-injection=enabled --overwrite
kubectl rollout restart deploy/demo -n demo
kubectl get pods -n demo -w

Injection happens only at pod creation, so existing pods must be restarted. You should see 2/2 in the READY column: the app container plus istio-proxy.

Verify:

powershell
kubectl get pod -n demo -o jsonpath="{.items[0].spec.containers[*].name}"
istioctl proxy-status | Select-String demo

Expected: demo istio-proxy, and the pod listed as SYNCED.

Why this matters in an interview: the sidecar intercepts all inbound and outbound traffic. Your Actuator probes are called by the kubelet, and Istio rewrites probe paths so the kubelet’s HTTP checks still work when mTLS is strict. Check it:

powershell
kubectl get pod -n demo -o yaml | Select-String "readinessProbe" -Context 0,6

You’ll see the probe path rewritten to something like /app-health/demo/readyz on port 15020. That’s Istio’s probe rewrite, and it’s the classic “why did my probe path change?” question.

C3: Gateway and VirtualService

Create deploy/istio/gateway.yaml:

yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: demo-gateway
  namespace: demo
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "demo.local"
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: demo
  namespace: demo
spec:
  hosts:
    - "demo.local"
  gateways:
    - demo-gateway
  http:
    - route:
        - destination:
            host: demo-demo.demo.svc.cluster.local
            port:
              number: 80

Check the Service name first. The Helm helper names the Service <release>-<chart>, unless the release name contains the chart name. Run:

powershell
kubectl get svc -n demo

Put the real name in host:. If it says demo, use demo.demo.svc.cluster.local.

Apply and test:

powershell
kubectl apply -f deploy/istio/gateway.yaml
kubectl port-forward -n istio-system svc/istio-ingressgateway 8088:80

In a second window (the Host header is how the gateway chooses the route):

powershell
Invoke-RestMethod -Uri http://localhost:8088/hello -Headers @{Host="demo.local"}

Expected: Hello from demo-.... Try without the header and you’ll get a 404, which proves the gateway routes by host.

C4: Observe in Kiali
powershell
kubectl port-forward -n istio-system svc/kiali 20001:20001

Generate some traffic (1..50 | % { Invoke-RestMethod http://localhost:8088/hello -Headers @{Host="demo.local"} }), then open http://localhost:20001, choose the demo namespace and the Graph view. Take a screenshot for your doc.

C5: mTLS (we’ll do after C3 works)

PeerAuthentication in STRICT mode, and a test showing a non-mesh pod being rejected. We’ll cover that in the next message.

Part C checkpoint (for after you finish)
What does sidecar injection add, and why must pods be restarted?
Why did the READY column change from 1/1 to 2/2?
What is the difference between a Gateway and a VirtualService?
Why does the request need a Host header?
Why is the ingress gateway <pending>, and how do you reach it on kind?
What does Istio do to health probes, and why?



## 2026-11-10: 503 from Istio ingress gateway
- **Symptom:** 503 via gateway with correct Host header (a wrong Host would give 404)
- **Diagnosis:** compared `kubectl get svc -n demo` with the VirtualService destination host
- **Root cause:** VirtualService pointed to demo-demo.demo.svc.cluster.local, but the
  Helm helper named the Service `demo` (release name contains chart name, so no duplication)
- **Fix:** changed destination host to demo.demo.svc.cluster.local and reapplied
- **Lesson:** 404 = no route matched; 503 = route matched but upstream unavailable.
  Never guess a Helm-generated name: read it from `kubectl get svc`, or better, use
  `helm template` to see it before writing dependent config.

  Interview takeaway

“I hit a 503 at the Istio gateway. Because it was a 503 and not a 404, I knew the Host route matched and the upstream was the problem. I compared the Service name against the VirtualService destination and found that Helm’s naming helper had produced demo rather than demo-demo. In a real setup I’d avoid that by templating the VirtualService from the same chart helper so the names can’t drift.”