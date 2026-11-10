---
layout: default
title: Block 2, Part C, Gateway Working, Sidecar Confirmed
parent: 8. Spring Boot Platform Lab
nav_order: 8
---

Part C: Gateway Working, Sidecar Confirmed

Both results are what we wanted.

Hello from demo-7fcfff4678-sklt9: the request went from your laptop, through the port-forward, into the Istio ingress gateway, matched Host: demo.local, and reached the pod.
2/2 Running: the app container plus istio-proxy. The pod is in the mesh.
Restarts 0, age 37m: the sidecar injection happened without trouble, and the pod has been stable since.

Fixing the Service name was the whole problem. Remember to add the troubleshooting entry.

C2 verification: capture the evidence

These prove the sidecar is really doing its job, and they make good doc material:

powershell
kubectl get pod -n demo -o jsonpath="{.items[0].spec.containers[*].name}"
istioctl proxy-status | Select-String "demo|ingressgateway"
kubectl get pod -n demo -o yaml | Select-String "readinessProbe" -Context 0,6

Expected:

demo istio-proxy
Both the gateway and your demo pod listed as SYNCED
The readiness probe path rewritten to something like /app-health/demo/readyz on port 15020. This is Istio’s probe rewrite: the sidecar answers the kubelet’s probe and forwards it to your real /actuator/health/readiness. It is the classic “why did my probe path change?” question. The rewrite also keeps probes working under strict mTLS, because the kubelet has no mesh certificate.

Also confirm the routing config as the gateway sees it:

powershell
istioctl proxy-config routes deploy/istio-ingressgateway -n istio-system | Select-String "demo"
C4: See it in Kiali

Keep the gateway port-forward running (port 8088), and in a second terminal:

powershell
kubectl port-forward -n istio-system svc/kiali 20001:20001

In a third window, generate traffic:

powershell
1..100 | ForEach-Object { Invoke-RestMethod http://localhost:8088/hello -Headers @{Host="demo.local"} | Out-Null; Start-Sleep -Milliseconds 200 }

Open http://localhost:20001, go to Graph, select namespace demo, and set the display to show Traffic animation and Security (the padlock icon will matter after mTLS). You should see istio-ingressgateway → demo. Take a screenshot for your doc.

C5: mTLS STRICT, and proving it

Create deploy/istio/peer-authentication.yaml:

yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: demo
spec:
  mtls:
    mode: STRICT
powershell
kubectl apply -f deploy/istio/peer-authentication.yaml

Test 1: a pod inside the mesh still works. The gateway request should still return Hello from ...:

powershell
Invoke-RestMethod http://localhost:8088/hello -Headers @{Host="demo.local"}

Test 2: a pod outside the mesh is rejected. Create a namespace with no injection and call the service from there:

powershell
kubectl create namespace outsider
kubectl run curl -n outsider --rm -it --image=curlimages/curl --restart=Never -- curl -sv --max-time 5 http://demo.demo.svc.cluster.local/hello

Expected: a connection reset or empty reply (Recv failure: Connection reset by peer), because the sidecar requires a mesh certificate and plain HTTP from outside is refused.

Test 3: prove it’s the policy. Switch to permissive and repeat Test 2:

powershell
kubectl patch peerauthentication default -n demo --type merge -p '{"spec":{"mtls":{"mode":"PERMISSIVE"}}}'

Now the outsider call should succeed. Switch back to STRICT afterwards. This before/after comparison is the evidence for your doc.

Clean up: kubectl delete namespace outsider

Part C checkpoint answers
What does sidecar injection add, and why restart pods? A mutating admission webhook adds the istio-proxy (Envoy) container and an init step that redirects traffic through it. Webhooks run only at pod creation, so existing pods need a restart.
Why 1/1 to 2/2? There are now two containers in the pod, both must be Ready.
Gateway vs VirtualService? The Gateway opens a port and host on the ingress proxy (the “door”). The VirtualService defines where matching traffic goes (the “routing rules”), and binds to the Gateway.
Why the Host header? The Gateway and VirtualService match on host demo.local. Without a matching host, there is no route and you get a 404.
Why <pending>, and how to reach it on kind? There’s no cloud load balancer to assign an external IP. Use kubectl port-forward, or MetalLB, or map ports in the kind config.
What does Istio do to probes? It rewrites them to go through the sidecar’s agent (port 15020), so the kubelet’s plain HTTP checks keep working under strict mTLS.
Commit and document
powershell
git add deploy/istio
git commit -m "block2: istio gateway, virtualservice, strict mtls"
git tag block-2-done
git push origin main --tags

In 02-kind-helm-istio.md, add a Part C section with: the 503 diagnosis story, the fixed Hello response, the 2/2 pod output, the probe rewrite output, the Kiali screenshot, and the mTLS STRICT vs PERMISSIVE comparison.

What to send me
The three verification outputs (container names, proxy-status, probe rewrite)
Result of mTLS Test 2 (outsider rejected) and Test 3 (permissive succeeds)

Then we move to Block 3: GitHub Actions, where the pipeline will build, test, and push the image to GHCR so the cluster pulls from a registry instead of kind load. That also lets us do the optional extension of moving the Gateway and VirtualService into the Helm chart.


mTLS Proven: Both Results Captured

Your two runs are the before/after comparison.

Mode	Outsider pod (no sidecar, plain HTTP)	Your output
PERMISSIVE	Accepted	HTTP/1.1 200 OK, Hello from demo-7fcfff4678-sklt9
STRICT	Rejected	Recv failure: Connection reset by peer
What the output shows
PERMISSIVE run: the response headers include server: istio-envoy and x-envoy-upstream-service-time: 1. The outsider pod has no sidecar, yet the request was answered by the destination pod’s Envoy, which accepted plain HTTP because permissive mode allows both plaintext and mTLS.
STRICT run: the TCP connection was established (Established connection) and the request was sent, but the destination sidecar reset it. The TLS-less request has no mesh certificate, so the sidecar drops it before it reaches your app. The app never saw the request, so the enforcement happens at the proxy, not in your code.
Your kubectl apply -f edit worked: peerauthentication ... configured confirms the declarative route replaced the broken PowerShell patch. The file in Git is now the source of truth.

Make sure deploy/istio/peer-authentication.yaml says mode: STRICT before you commit, since that’s the state you want in the repo. Check with:

powershell
kubectl get peerauthentication default -n demo -o jsonpath="{.spec.mtls.mode}"

It should print STRICT. Also confirm the mesh itself still works under STRICT (a gateway request should return Hello from ...):

powershell
Invoke-RestMethod http://localhost:8088/hello -Headers @{Host="demo.local"}
Part C checkpoint

You can now answer all six checkpoint questions from experience. The one worth rehearsing aloud:

“I enabled STRICT mTLS on the namespace and proved it: a pod outside the mesh got its connection reset, while the same call succeeded in PERMISSIVE mode. In-mesh traffic through the gateway kept working because the sidecars exchange certificates automatically. I made the change declaratively in Git rather than patching, after hitting a PowerShell quoting issue with an inline JSON patch.”

Commit, tag, document
powershell
git add deploy/istio
git commit -m "block2: istio gateway, virtualservice, strict mtls"
git tag block-2-done
git push origin main --tags

In 02-kind-helm-istio.md, Part C should now contain:

The 503 diagnosis story (Service name mismatch)
The working Hello response and 2/2 pod
The probe rewrite output (if you ran the verification commands)
This PERMISSIVE vs STRICT table with your real outputs
The Kiali screenshot, if you took one

Add the PowerShell quoting entry to the troubleshooting log too.

Block 2 is complete

Summary of what you can now claim, truthfully:

Plain manifests with startup/readiness/liveness probes and graceful shutdown, proven with 1550 requests and zero failures during a rollout
A Helm chart with per-environment values, validated with lint/template, with install, upgrade, and rollback tested
Istio sidecar injection, Gateway and VirtualService routing, and STRICT mTLS enforcement with evidence
Three real troubleshooting stories: ErrImagePull on kind, the gateway 503, and the PowerShell quoting issue
Next: Block 3, GitHub Actions

We’ll build the pipeline in the lab repo:

Workflow: checkout, Java setup with Maven cache, mvn verify, Docker build, push to GHCR
Tag images with the Git SHA
Update the image tag in the Helm values (the GitOps step, using yq)
Have the cluster pull from the registry using an imagePullSecret, replacing kind load

Before we start, send me:

powershell
git remote -v
git branch --show-current

Also confirm whether your Spring Boot project sits in app/ (as planned) or at the repo root, because the workflow paths and Docker build context depend on it. Reply “Block 2 complete” along with those answers and we’ll begin.