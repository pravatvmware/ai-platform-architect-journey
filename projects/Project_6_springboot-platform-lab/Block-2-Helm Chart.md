---
layout: default
title: Block 2: Part B: Helm Chart
parent: 8. Spring Boot Platform Lab
nav_order: 6
---

You now know every field in the raw YAML, so Helm will make sense: it is the same YAML with the variable parts pulled out into values.

B1: Scaffold the chart

From the lab repo root:

powershell
cd deploy/helm
helm create demo
cd demo

Check helm version first. Then delete the files we don’t need:

powershell
Remove-Item -Recurse templates/tests
Remove-Item templates/hpa.yaml, templates/serviceaccount.yaml, templates/NOTES.txt
Remove-Item values.yaml

Keep Chart.yaml, templates/_helpers.tpl, templates/deployment.yaml, templates/service.yaml. We’ll rewrite the deployment and service so you see every line.

B2: Chart.yaml
yaml
apiVersion: v2
name: demo
description: Spring Boot demo service
type: application
version: 0.1.0        # chart version (bump when the chart changes)
appVersion: "1"       # app/image version
B3: values.yaml (defaults)
yaml
replicaCount: 2

image:
  repository: demo
  tag: "1"
  pullPolicy: IfNotPresent

springProfile: dev

service:
  port: 80

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    memory: 768Mi

probes:
  startup:
    failureThreshold: 30
    periodSeconds: 5
  readiness:
    periodSeconds: 10
  liveness:
    periodSeconds: 10

terminationGracePeriodSeconds: 45
preStopSleepSeconds: 5
B4: templates/deployment.yaml

Replace the contents with:

yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "demo.fullname" . }}
  labels:
    {{- include "demo.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "demo.selectorLabels" . | nindent 6 }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        {{- include "demo.selectorLabels" . | nindent 8 }}
    spec:
      terminationGracePeriodSeconds: {{ .Values.terminationGracePeriodSeconds }}
      containers:
        - name: demo
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: {{ .Values.springProfile | quote }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          startupProbe:
            httpGet:
              path: /actuator/health/liveness
              port: http
            periodSeconds: {{ .Values.probes.startup.periodSeconds }}
            failureThreshold: {{ .Values.probes.startup.failureThreshold }}
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: http
            periodSeconds: {{ .Values.probes.readiness.periodSeconds }}
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: http
            periodSeconds: {{ .Values.probes.liveness.periodSeconds }}
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "{{ .Values.preStopSleepSeconds }}"]
B5: templates/service.yaml
yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "demo.fullname" . }}
  labels:
    {{- include "demo.labels" . | nindent 4 }}
spec:
  selector:
    {{- include "demo.selectorLabels" . | nindent 4 }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
B6: Per-environment values

Create two small override files next to values.yaml:

values-dev.yaml

yaml
replicaCount: 1
springProfile: dev
resources:
  requests: {cpu: 100m, memory: 512Mi}
  limits: {memory: 768Mi}

values-prod.yaml

yaml
replicaCount: 3
springProfile: prod
resources:
  requests: {cpu: 500m, memory: 768Mi}
  limits: {memory: 1Gi}
B7: Validate before installing

Run these in order. Each catches a different class of mistake:

powershell
helm lint .
helm template demo . -f values-dev.yaml
helm template demo . -f values-prod.yaml | Select-String "replicas|memory|SPRING"

lint checks chart structure, template renders the final YAML locally with no cluster needed. Compare the dev and prod renders to see the values override at work.

B8: Replace the raw deployment with the Helm release

The plain manifest and the chart would collide on the same names, so remove the raw one first. The demo namespace is part of the raw manifest, so recreate it:

powershell
kubectl delete -f ../../k8s/demo.yaml
kubectl create namespace demo
helm install demo . -n demo -f values-dev.yaml
helm list -n demo
kubectl get pods -n demo

Then try the Helm lifecycle:

powershell
# upgrade: scale to prod values
helm upgrade demo . -n demo -f values-prod.yaml
kubectl get pods -n demo

# history and rollback
helm history demo -n demo
helm rollback demo 1 -n demo
helm history demo -n demo
Part B checkpoint
Why do helm template and helm lint come before install?
What is the difference between values.yaml and values-prod.yaml, and which wins?
What is the difference between chart version and appVersion?
What does helm rollback do, and how is it different from Argo CD’s rollback by git revert?
Why is the image tag a value and not hardcoded?
What to send me
Output of helm lint . and the helm version
The helm list -n demo and kubectl get pods -n demo after install
The helm history output after the rollback
Any error text

Then we’ll move to Part C: Istio, adding sidecar injection, a Gateway, and a VirtualService, plus the sidecar and probe issues you should know about.

helm lint .
==> Linting .
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
(.venv) PS D:\PRAVAT\AI-Platform-Architect\Spring-Boot-Platform-Lab\deploy\helm\demo> helm version
version.BuildInfo{Version:"v4.3.1", GitCommit:"c0d08d0d6d9424d4a14febb5e8a3e51b0dd00dff", GitTreeState:"clean", GoVersion:"go1.27.2", KubeClientVersion:"v1.37"}
(.venv) PS D:\PRAVAT\AI-Platform-Architect\Spring-Boot-Platform-Lab\deploy\helm\demo> helm list -n demo
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
demo    demo            3               2026-11-10 21:17:35.1374041 +0530 IST   deployed        demo-0.1.0      1          
(.venv) PS D:\PRAVAT\AI-Platform-Architect\Spring-Boot-Platform-Lab\deploy\helm\demo> kubectl get pods -n demo
NAME                    READY   STATUS    RESTARTS   AGE
demo-64476db547-zh52m   1/1     Running   0          79s
(.venv) PS D:\PRAVAT\AI-Platform-Architect\Spring-Boot-Platform-Lab\deploy\helm\demo> helm history
Error: "helm history" requires 1 argument

Usage:  helm history RELEASE_NAME [flags]
(.venv) PS D:\PRAVAT\AI-Platform-Architect\Spring-Boot-Platform-Lab\deploy\helm\demo> helm history demo -n demo
REVISION        UPDATED                         STATUS          CHART           APP VERSION     DESCRIPTION     
1               Tue Nov 10 21:14:38 2026        superseded      demo-0.1.0      1               Install complete
2               Tue Nov 10 21:16:24 2026        superseded      demo-0.1.0      1               Upgrade complete
3               Tue Nov 10 21:17:35 2026        deployed        demo-0.1.0      1               Rollback to 1

Part B Result: Helm Lifecycle Worked

Your output shows a full install → upgrade → rollback cycle.

What your output proves
helm lint: 0 charts failed. The icon is recommended line is an INFO, not a problem. Ignore it.
Helm v4.3.1: the commands behave the same as Helm 3 for everything we’re doing here.
helm history:
Revision 1: Install complete (dev values, 1 replica)
Revision 2: Upgrade complete (prod values, 3 replicas)
Revision 3: Rollback to 1. Rollback does not rewind the counter. It creates a new revision whose content equals revision 1. That’s why you see 3 and not 1.
kubectl get pods: one pod 1/1 Running, matching values-dev.yaml (replicaCount: 1). That confirms the rollback restored the dev configuration.

Note that revisions 1 to 3 all show demo-0.1.0 / 1. The chart version and app version didn’t change, only the values did. That’s the answer to checkpoint question 3: version is the chart’s own version (bump it when templates change), and appVersion describes the application image being deployed.

Quick verification (2 minutes)

Run these to capture evidence for your doc:

powershell
helm get values demo -n demo
helm get manifest demo -n demo | Select-String "replicas|memory|SPRING" -Context 0,1
kubectl get deploy demo -n demo -o jsonpath="{.spec.replicas}"

The first shows the dev override values in effect. The others confirm replicas and memory match values-dev.yaml.

Also re-run the zero-downtime test against the Helm-managed deployment. The chart should behave exactly like the raw YAML:

powershell
kubectl run loadgen -n demo --image=curlimages/curl --restart=Never -- sh -c "while true; do curl -s -o /dev/null -w '%{http_code}\n' http://demo-demo/hello; sleep 0.3; done"

Note the Service name. The demo.fullname helper from helm create joins the release name and chart name, giving demo-demo unless the names are the same, in which case Helm deduplicates it to demo. Check with kubectl get svc -n demo and use the real name in the URL. If you see 000 in the loadgen logs, the wrong service name is the usual reason.

Then:

powershell
Start-Sleep 15
helm upgrade demo . -n demo -f values-prod.yaml
kubectl rollout status deploy/demo -n demo
kubectl logs loadgen -n demo | Group-Object | Select-Object Name, Count
kubectl delete pod loadgen -n demo

An upgrade is a rollout, so this tests Helm-driven deployments for dropped requests.

Part B checkpoint answers
Why lint and template before install? They catch mistakes before touching the cluster. lint checks chart structure and syntax. template renders the final YAML locally, so you can review exactly what will be applied. In CI, these are the cheap gates that fail fast.
values.yaml vs values-prod.yaml, which wins? values.yaml holds defaults. A file passed with -f overrides it, and --set overrides both. Later -f files override earlier ones. Maps merge key by key, but lists are replaced whole.
version vs appVersion: version is the chart package version (SemVer), bumped when templates or defaults change. appVersion records the application version being deployed. They move independently.
helm rollback vs Argo CD git revert: Helm rollback is an imperative action against the cluster, stored in release secrets in the cluster. It leaves Git out of date, which causes drift. In GitOps you revert in Git and Argo reconciles, so Git remains the source of truth and the audit trail. Helm is the packaging tool, and Argo CD (or Helm used by Argo) is the delivery mechanism.
Why is the image tag a value? One chart serves every environment and every release. CI only changes the tag (to the Git SHA) in the deployment repo values, and Argo CD deploys that. The same immutable image gets promoted without rebuilding.

Interview line:

“I wrote the Helm chart so everything environment-specific, like replicas, resources, profile, and image tag, lives in values files. I validated with lint and template before installing, and tested upgrade and rollback. In a GitOps setup the image tag in the deployment repo values is the only thing the pipeline changes.”

Commit and document
powershell
cd ../../..
git add deploy/helm
git commit -m "block2: helm chart with dev and prod values"

In 02-kind-helm-istio.md, add a Part B section with: the helm lint output, helm template dev vs prod comparison (replicas and memory lines), the helm history table, and a note explaining why rollback produced revision 3.

Add one entry to the troubleshooting log if anything went wrong while writing the chart. If nothing did, skip it. Don’t invent entries.

Part C: Istio (about 45 min)

Do the verification above first, then continue. We’ll cover:

Enable sidecar injection on the demo namespace and restart pods (they become 2/2).
Add a Gateway and VirtualService to route external traffic to the service.
Observe the sidecar and probe behavior with Spring Boot.
Add mTLS with PeerAuthentication.

Before we start, please send me:

powershell
kubectl get pods -n istio-system
istioctl version
kubectl get svc -n istio-system