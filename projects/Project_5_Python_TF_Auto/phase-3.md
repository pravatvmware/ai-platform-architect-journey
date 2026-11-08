---
layout: default
title: Phase 3 - Enterprise Security
parent: 7. Project 5 - Python & Terraform Automation
nav_order: 3
---

# Phase 3: Enterprise Architecture & Security
{: .no_toc }

This phase introduces **Policy-as-Code** into the pipeline. In enterprise environments, infrastructure code is never applied blindly. This phase integrates **Checkov** to scan the generated Terraform plan. If the scanner detects security vulnerabilities (e.g., exposed ports, missing encryption), the Python orchestrator intercepts the failure and halts the pipeline before any infrastructure is provisioned.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

Install the Checkov policy-as-code scanner in your Python environment:

```bash
pip install checkov
```

Note: Your directory structure remains the same as Phase 2 (config.json and templates/main.tf.j2 do not change).

## The Enterprise Gate Orchestrator
Update your deploy.py script. This version introduces the run_security_scan() function, which acts as a strict gatekeeper between the terraform plan and terraform apply stages.

## Execution & Verification
Run the Python pipeline:

```Bash
python deploy.py
```

### Expected Output
Because this framework currently targets local Docker infrastructure, Checkov may pass immediately (as it heavily targets AWS/Azure/GCP defaults). The terminal will output:✅ SECURITY SCAN PASSED. No policy violations found.
and proceed to safely deploy the containers.

In a production Azure environment, this exact same mechanism would flag issues like unencrypted storage accounts or public IP exposures, halting the pipeline before a costly or insecure deployment occurs.