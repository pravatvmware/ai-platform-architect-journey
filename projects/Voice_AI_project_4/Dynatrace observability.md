---
title: "Automated rollback driven by Dynatrace observability"
parent: "6. Project 4 gcp voice AI"
nav_order: 6
---

# Project 4: Automated rollback driven by Dynatrace observability

To implement the automated rollback driven by Dynatrace observability, you need to configure Harness to actively poll Dynatrace metrics during the deployment phase and define a failure strategy that triggers the rollback.

Here is the step-by-step implementation and the corresponding Harness YAML configuration.

## 1. Set Up the Dynatrace Connector in Harness
First, Harness needs secure access to your Dynatrace tenant.

* In Harness, navigate to Project Setup > Connectors > New Connector.

* Select Dynatrace and input your Dynatrace Tenant URL (e.g., https://{your-environment-id}.live.dynatrace.com).

* Store your Dynatrace API Token (which requires Read metrics and Access problem and event feed, metrics, and topology scopes) in Harness Secret Manager and reference it in the connector.

## 2. Define the Monitored Service and Health Source
You must tell Harness exactly what metrics define a "healthy" Voice AI inference.

* Create a Monitored Service in Harness linking your environment (e.g., prod) to your Voice AI application.

* Add a Health Source mapping to Dynatrace. You will define specific Service Level Indicators (SLIs) using PromQL or Dynatrace Metric Queries (DQL).

* **Metric 1:** Inference Latency (e.g., builtin:service.response.time).

* **Metric 2:** Error Rate (e.g., builtin:service.errors.total.count).

## 3. Implement the Continuous Verification (CV) Step
Within your pipeline's Deployment Stage, add a Continuous Verification step immediately after deploying the canary pod. Harness uses this step to query the health source over a specified duration (e.g., 10 minutes) and leverages machine learning to analyze the Dynatrace metrics for deviations against the stable baseline.

## 4. Configure the Automated Rollback Strategy
You define a Failure Strategy at the pipeline or step level. If the Continuous Verification step fails (meaning Dynatrace detected a latency spike or error breach), Harness automatically triggers the Rollback steps.

Here is how this integration looks in the Harness Pipeline YAML:

```yaml
pipeline:
  name: Voice AI Canary with Dynatrace Verification
  stages:
    - stage:
        name: Canary Deployment
        type: Deployment
        spec:
          infrastructure:
            environmentRef: prod-env
            infrastructureDefinition:
              type: KubernetesDirect
              spec:
                connectorRef: gcp-gke-connector
                namespace: prod-voice-ai
          execution:
            steps:
              # 1. Deploy the 10% Canary Pods
              - step:
                  type: K8sCanaryDeploy
                  name: Deploy Canary
                  spec:
                    skipDryRun: false
                    
              # 2. Shift 10% of Istio Traffic to the Canary
              - step:
                  type: IstioTrafficShift
                  name: Shift 10% Traffic
                  spec:
                    weight: 10
                    
              # 3. Dynatrace Continuous Verification
              - step:
                  type: Verify
                  name: Dynatrace Verification
                  spec:
                    type: ContinuousVerification
                    verifyType: Canary
                    sensitivity: MEDIUM
                    duration: 10m # Analyze Dynatrace metrics for 10 minutes
                    healthSources:
                      - dynatrace-voice-ai-health-source # References the defined SLIs
                      
            # 4. Automated Rollback Triggered on Verification Failure
            rollbackSteps:
              - step:
                  type: IstioTrafficShift
                  name: Revert Traffic to Baseline
                  spec:
                    weight: 0 # Instantly routes 100% back to v1
              - step:
                  type: K8sDelete
                  name: Scale Down Faulty Canary
                  spec:
                    deleteResources:
                      - Deployment/voice-ai-v2
        failureStrategies:
          - onFailure:
              errors:
                - Verification # If the Dynatrace verification step fails
              action:
                type: Rollback # Trigger the rollbackSteps defined above
```


* This configuration ensures that if Dynatrace's Davis AI detects an anomaly during the 10-minute verification window, the pipeline automatically aborts, routes all Istio traffic back to the stable version, and cleans up the faulty pods, protecting the financial institution's live users.

* Leverage Davis AI to Analyze your System before Things Break
This video provides an overview of how Dynatrace Davis AI analyzes system health and detects anomalies before they cause widespread impact.

Ref: [Leverage Davis AI to Analyze your System before Things Break](https://www.youtube.com/watch?v=JKlSYirBViE)