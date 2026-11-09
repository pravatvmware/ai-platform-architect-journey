---
title: "Map out how a Harness pipeline executes a Canary deployment using these Istio resources"
parent: "6. Project 4 gcp voice AI"
nav_order: 3
---

# Project 4: Map out how a Harness pipeline executes a Canary deployment using these Istio resources

## 1. Artifact & Manifest Retrieval
The pipeline triggers when a new Voice AI container image is pushed to Google Artifact Registry. Harness retrieves this new image tag and pulls the associated Kubernetes manifests (Deployments, Services) and Istio manifests (VirtualService, DestinationRule) from your Git repository.

## 2. Deploying the Canary Pods (Subset v2)
Harness connects to your GKE cluster and deploys the new version of your Voice AI application as a distinct Kubernetes Deployment (e.g., voice-ai-v2).

* At this stage, the Istio DestinationRule is updated to define both the stable subset (v1) and the canary subset (v2).

* Because the VirtualService has not yet been modified, 100% of live user traffic continues to route to v1. The v2 pods are running but isolated.

## 3. The Initial Traffic Shift (Modifying the VirtualService)
Harness automatically modifies the Istio VirtualService to begin the canary test.

* It updates the routing weights in the YAML, shifting a predetermined percentage of traffic—for example, 10%—to the new version.

* The VirtualService now directs the Istio Ingress Gateway to route 90% of requests to the v1 subset and 10% to the v2 subset.

## 4. Automated Verification (Dynatrace Integration)
This is where Harness excels for financial sector compliance. Instead of relying on manual testing, Harness enters a verification phase.

* Harness queries Dynatrace to monitor the specific performance of the v2 pods processing the 10% traffic.

* It checks key Service Level Indicators (SLIs) such as inference latency, HTTP 500 error rates, and CPU/memory utilization.

* If Dynatrace's Davis AI detects anomalies or if the metrics breach defined thresholds, Harness automatically aborts the pipeline, instantly reverts the VirtualService to route 100% of traffic back to v1, and scales down the faulty v2 pods.

## 5. Incremental Promotion
If the initial 10% canary passes the Dynatrace health checks, Harness progresses through the defined pipeline stages.

* It updates the VirtualService weights incrementally (e.g., 25%, then 50%, then 75%), running continuous Dynatrace verifications at each step to ensure the new AI model handles the increased load gracefully.

## 6. Finalization and Cleanup
Once the canary reaches 100% traffic and passes final verification, the deployment is considered successful.

* Harness permanently updates the baseline VirtualService to route all traffic to the new version.

* It scales the old v1 Deployment down to zero to free up GKE cluster resources.

* The v2 version now becomes the new stable baseline for future deployments.
