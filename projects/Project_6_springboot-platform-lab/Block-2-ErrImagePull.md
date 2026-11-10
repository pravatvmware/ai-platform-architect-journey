---
layout: default
title: Block 2: Diagnosing ErrImagePull: This Is the Exact Case I Warned About
parent: 8. Spring Boot Platform Lab
nav_order: 5
---

Diagnosing ErrImagePull: This Is the Exact Case I Warned About

The pods can’t find demo:1 inside the kind node. Docker Desktop has the image, but the kind node (a separate container with its own image store) doesn’t. That’s the A1 step, and this is a good troubleshooting entry for your log.

Step 1: Confirm the cause
powershell
kubectl describe pod -n demo -l app=demo | Select-String -Pattern "Failed|Back-off|pull|repository"

You’ll likely see something like pull access denied or repository does not exist. Kubernetes tried to pull docker.io/library/demo:1 from the internet, which doesn’t exist.

Step 2: Find your cluster name and load the image
powershell
kind get clusters

Then, using that name (for example kind):

powershell
kind load docker-image demo:1 --name <your-cluster-name>

Check the image is inside the node:

powershell
docker exec <your-cluster-name>-control-plane crictl images | Select-String demo

You should see docker.io/library/demo   1. If the cluster has worker nodes, kind load copies to all of them. Check with kubectl get nodes.

Step 3: Make the pods retry

Pods in ImagePullBackOff retry on their own with growing delays, but you can force it immediately:

powershell
kubectl rollout restart deploy/demo -n demo
kubectl get pods -n demo -w

You should now see 0/1 Running and then 1/1 Running.

If it still fails
Symptom	Likely cause	Fix
crictl images shows nothing for demo	Wrong cluster name in --name	Use the exact name from kind get clusters
Image present but still ErrImagePull	Tag mismatch (the manifest says demo:1)	Run docker images demo and confirm the tag is 1
ErrImageNeverPull	imagePullPolicy: Never somewhere	We set IfNotPresent, so check the YAML was applied
kind load fails on Docker Desktop with a containerd image store error	Docker Desktop’s containerd-based image store can break kind load docker-image	Use docker save demo:1 -o demo.tar then kind load image-archive demo.tar --name <name>

The last row is a known quirk on newer Docker Desktop versions, so try the archive method if the normal load errors out.

Write this into your troubleshooting log
markdown
## 2026-11-10: ErrImagePull on kind
- **Symptom:** pods in ErrImagePull / ImagePullBackOff
- **Diagnosis:** kubectl describe pod showed pull attempt against docker.io for demo:1
- **Root cause:** image existed in Docker Desktop but not in the kind node's image store
- **Fix:** kind load docker-image demo:1 --name <cluster>, then rollout restart
- **Lesson:** kind nodes are separate containers. In real environments the image would come from a registry (Artifactory/GHCR), which is what Block 3's pipeline will provide.

That last lesson is a nice bridge to your interview story: locally you side-load, but in the real flow the pipeline pushes to a registry and the cluster pulls from it with an imagePullSecret.

Send me the output of kind get clusters and the pod status after the restart. Once they’re 1/1 Running, continue with A3 onward.

The image is now inside the node, so the cause is confirmed and fixed. docker.io/library/demo   1   d6c553ea02930   138MB is the line that matters. Your cluster is enterprise-sandbox (node enterprise-sandbox-control-plane), and it also holds the Online Boutique images from an earlier lab, which is why the output is long. That’s fine, but keep it in mind: we’ll use the demo namespace so nothing collides.

Step 1: Make the pods retry

The pods are sitting in ImagePullBackOff with a growing delay, so force a fresh start:

powershell
kubectl rollout restart deploy/demo -n demo
kubectl get pods -n demo -w

Expect 0/1 Running for a short while (JVM boot plus the startup probe), then 1/1 Running for both pods. Stop watching with Ctrl+C.

If the pods are still failing after about a minute, check for this:

powershell
kubectl describe pod -n demo -l app=demo | Select-String -Pattern "Failed|Back-off|Pulled|Started"

You want to see Pulled and Started, not Failed.

Step 2: Continue Part A

Once both pods are 1/1 Running, run these in order:

powershell
# A3: the object chain
kubectl get deploy,rs,pods,svc,endpoints -n demo

# A4: real load balancing from inside the cluster
kubectl run curl -n demo --rm -it --image=curlimages/curl --restart=Never -- sh -c "for i in 1 2 3 4 5 6; do curl -s http://demo/hello; echo; done"

The curl image comes from Docker Hub, so the node needs internet access to pull it. If it hangs with ImagePullBackOff, tell me and we’ll side-load it the same way.

What to look for:

Endpoints should list two pod IPs. That list is exactly the set of Ready pods, which is how readiness controls traffic.
The curl loop should print both pod names (Hello from demo app demo-75455b9665-...). Your app’s greeting includes “demo app” followed by the hostname, so on Kubernetes the hostname is the pod name.

Then do the port-forward checks (A4/A5) and the rollout test (A6) with the load generator.

Bonus experiment (worth doing for your doc)

Since you now have a working baseline, try breaking the graceful-shutdown chain and compare:

Run the A6 load generator and rollout restart: expect all 200.
Remove the lifecycle.preStop block and terminationGracePeriodSeconds, set maxUnavailable: 1, apply, and repeat the rollout while the loadgen runs.
Compare the status-code counts. You may see a few 000/503 responses. Even if you don’t (small clusters are forgiving), you can describe what the test is designed to catch.

Restore the original manifest afterwards.

Update your troubleshooting log

Add the cluster name and the exact command you used:

markdown
- **Fix:** kind load docker-image demo:1 --name enterprise-sandbox, verified with
  docker exec enterprise-sandbox-control-plane crictl images
What to send me next
The pod status after the restart (kubectl get pods -n demo)
The output of kubectl get deploy,rs,pods,svc,endpoints -n demo
The in-cluster curl output showing the pod names

Then we’ll do the rollout test and move to Part B (Helm chart).

kubectl describe pod -n demo -l app=demo | Select-String -Pattern "Failed|Back-off|Pulled|Started"

Annotations:      kubectl.kubernetes.io/restartedAt: 2026-11-10T20:20:32+05:30
      Started:      Tue, 10 Nov 2026 20:20:39 +0530
Annotations:      kubectl.kubernetes.io/restartedAt: 2026-11-10T20:20:32+05:30
      Started:      Tue, 10 Nov 2026 20:20:33 +0530

Both pods show a Started: timestamp and no Failed or Back-off lines, so the image pull is fixed and the containers are running. The restartedAt annotation is the rollout restart you triggered, and it’s why the old failing pods were replaced.

One thing is still unconfirmed: “Started” only means the container launched. The JVM still has to boot and pass the readiness probe before the pod is 1/1. Check that now:

powershell
kubectl get pods -n demo
kubectl get deploy,rs,pods,svc,endpoints -n demo

What you want to see:

Both pods show 1/1 Running.
The Deployment shows 2/2 ready.
The Endpoints entry for demo lists two IPs with port 8080.

If a pod is 0/1 Running, wait about 30 to 60 seconds, since Spring Boot startup plus the startup probe takes a little while. If it stays 0/1 after that, run:

powershell
kubectl describe pod -n demo -l app=demo | Select-String -Pattern "Readiness|Liveness|Startup|Unhealthy"
kubectl logs -n demo deploy/demo --tail=30

An Unhealthy event would mean a probe is failing, and the logs will show why.

Once both are 1/1, run the load balancing test:

powershell
kubectl run curl -n demo --rm -it --image=curlimages/curl --restart=Never -- sh -c "for i in 1 2 3 4 5 6; do curl -s http://demo/hello; echo; done"

You should see both pod names across the six lines.

Please send me:

The output of kubectl get deploy,rs,pods,svc,endpoints -n demo
The curl loop output

Then we’ll do the port-forward checks and the graceful rollout test, and after that move to Part B (Helm).

kubectl get deploy,rs,pods,svc,endpoints -n demo
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/demo   2/2     2            2           12m

NAME                              DESIRED   CURRENT   READY   AGE
replicaset.apps/demo-75455b9665   0         0         0       12m
replicaset.apps/demo-86b895d969   2         2         2       5m30s

NAME                        READY   STATUS    RESTARTS   AGE
pod/demo-86b895d969-j7dtz   1/1     Running   0          5m23s
pod/demo-86b895d969-rsfbf   1/1     Running   0          5m30s

NAME           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/demo   ClusterIP   10.96.161.71   <none>        80/TCP    12m

NAME             ENDPOINTS                           AGE
endpoints/demo   10.244.0.28:8080,10.244.0.29:8080   12m

Part A is healthy. Here is what your output shows:

Deployment 2/2 ready, 2 available: both replicas pass their readiness probes.
Two ReplicaSets: demo-75455b9665 (0 pods) is the old one from the failed ErrImagePull attempt. demo-86b895d969 (2 pods) is the one created by your rollout restart. Kubernetes keeps the old ReplicaSet at 0 for rollback history (kubectl rollout undo would scale it back up).
Endpoints 10.244.0.28:8080, 10.244.0.29:8080: these two IPs are exactly the two Ready pods. If a readiness probe failed, that pod’s IP would drop out of this list and the Service would stop sending it traffic.
Service ClusterIP 10.96.161.71:80: a stable virtual IP in front of the changing pod IPs.
Pod ages (5m30s and 5m23s): the 7-second gap shows the rolling update at work. With maxUnavailable: 0 and maxSurge: 1, the second pod was only created after the first was Ready.
Next: load balancing test
powershell
kubectl run curl -n demo --rm -it --image=curlimages/curl --restart=Never -- sh -c "for i in 1 2 3 4 5 6; do curl -s http://demo/hello; echo; done"

Expect both demo-86b895d969-j7dtz and demo-86b895d969-rsfbf across the six lines. Distribution is random, so six calls may favor one pod. Try 20 iterations if you only see one name.

Then: the graceful rollout test (A6)

Start the load generator:

powershell
kubectl run loadgen -n demo --image=curlimages/curl --restart=Never -- sh -c "while true; do curl -s -o /dev/null -w '%{http_code}\n' http://demo/hello; sleep 0.3; done"

Wait about 10 seconds for it to start, then trigger a rollout and wait for it to finish:

powershell
kubectl rollout restart deploy/demo -n demo
kubectl rollout status deploy/demo -n demo

Count the results:

powershell
kubectl logs loadgen -n demo | Group-Object | Select-Object Name, Count

Expected: only 200. Any 000, 502, or 503 means requests were dropped.

Clean up:

powershell
kubectl delete pod loadgen -n demo
Capture for your doc

Paste these into the Part A section of 02-kind-helm-istio.md:

The kubectl get deploy,rs,pods,svc,endpoints output above, with the notes about the two ReplicaSets and the Endpoints list.
The curl loop output showing both pod names.
The Group-Object counts from the rollout test.


Part A Result: Zero Dropped Requests

Both tests passed.

Load balancing

Both pods, rsfbf and j7dtz, answered, so the Service spreads traffic across the Ready endpoints. The split was 2 to 4 in six calls, which is normal for random distribution. Your app’s greeting now reads Hello from <pod-name>, so the pod name appears directly.

Rollout test

1550 requests, all 200, zero failures across a full rolling restart. Pods were replaced while traffic was flowing, and no request was dropped. That is the evidence that these pieces work together:

maxUnavailable: 0 keeps old pods until new ones are Ready.
The readiness probe keeps traffic away from a pod that isn’t up yet.
preStop: sleep 5 lets endpoint removal propagate before shutdown starts.
server.shutdown: graceful drains in-flight requests on SIGTERM.
terminationGracePeriodSeconds: 45 leaves room for the whole sequence.

One caveat for honesty in your doc: the loadgen pod already existed. My first command created it, but its creation output was cut off in your earlier paste, and your second attempt reported AlreadyExists. So the loadgen was running before you triggered the restart, which is fine. The 1550 requests cover the whole period from its creation, including the rollout. At 0.3 s per request that is about 8 minutes of traffic, so only part of it overlapped with the rollout window. The result is still valid (nothing failed), but to describe the test precisely, say “all 1550 requests during the test period returned 200, including a full rolling restart.”

If you want a tighter test, reset the counter and run it again:

powershell
kubectl delete pod loadgen -n demo
kubectl run loadgen -n demo --image=curlimages/curl --restart=Never -- sh -c "while true; do curl -s -o /dev/null -w '%{http_code}\n' http://demo/hello; sleep 0.3; done"
Start-Sleep 15
kubectl rollout restart deploy/demo -n demo
kubectl rollout status deploy/demo -n demo
kubectl logs loadgen -n demo | Group-Object | Select-Object Name, Count
kubectl delete pod loadgen -n demo
Optional: the contrast experiment

This makes a strong doc section, because it shows why each setting exists. Edit deploy/k8s/demo.yaml:

Remove the lifecycle.preStop block.
Remove terminationGracePeriodSeconds.
Set maxUnavailable: 1.
Remove server.shutdown: graceful is in the image, so skip that one unless you rebuild.

Apply, rerun the load test, and compare counts. A small cluster can be forgiving, so you may still see all 200. If so, write exactly that: “no failures observed at this scale, but the settings guard against the race between endpoint removal and SIGTERM.” Then restore the original manifest with kubectl apply -f.

Part A checkpoint answers
Why kind load? kind nodes are containers with their own image store, so Docker Desktop’s images are invisible to them. In real environments the image comes from a registry.
What does Endpoints show? The IPs of Ready pods only. A failing readiness probe removes that pod’s IP, so it stops receiving traffic without being restarted.
Why maxUnavailable: 0? Capacity never drops during a rollout. A new pod must be Ready before an old one is terminated.
Why must terminationGracePeriodSeconds exceed preStop plus the shutdown timeout? Kubernetes SIGKILLs the pod when the grace period ends. If it is shorter than 5 s + 30 s, in-flight requests are cut off during the drain.
Why no load balancing in port-forward? kubectl port-forward tunnels to a single pod and doesn’t go through the Service’s balancing.
Clean up and commit
powershell
kubectl delete pod loadgen -n demo
git add deploy/k8s/demo.yaml
git commit -m "block2: plain k8s manifests with probes and graceful shutdown"

Add the troubleshooting entry for ErrImagePull and paste the three outputs into the Part A section of 02-kind-helm-istio.md.