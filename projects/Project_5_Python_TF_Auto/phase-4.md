---
layout: default
title: Phase 4 - Drift Detection
parent: 7. Project 5 - Python & Terraform Automation
nav_order: 4
---

# Phase 4: Verification & Drift Detection
{: .no_toc }

In enterprise environments, infrastructure can "drift" from its Terraform code if someone manually modifies resources outside of the CI/CD pipeline (e.g., via the Azure Portal or AWS Console). 

This phase introduces an automated **Drift Detection Engine**. Using the **Python Docker SDK** (simulating cloud provider SDKs like Azure SDK or Boto3), the pipeline queries the live infrastructure daemon and compares it exactly against our declarative JSON configuration, logging any discrepancies and publishing an audit report.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

Install the official Docker SDK for Python in your virtual environment:

```bash
pip install docker
```

## Directory Structure
Add the new verify.py script to your root directory. Your project should now look like this:

```
project-5/
├── deploy.py
├── verify.py         <-- (New: Drift Detection Engine)
├── configs/
├── templates/
├── reports/          
└── infrastructure/
```

### 1. The Drift Detection Engine
Save this as verify.py. This script connects directly to the Docker API, bypassing Terraform entirely, to independently audit the live state of the infrastructure against your configs/<env>.json files.

### 2. Execution & Testing Drift
To test this engine, you must first have a running baseline deployed via Phase 3.

Step 1: Verify the Baseline (No Drift)
Run the script against an active environment:

```Bash
python verify.py --env dev
```

#### Expected Output: The script will verify that the running containers match your dev.json and generate a report indicating ✅ PERFECT MATCH.

## Step 2: Simulate a Security Breach (Create Drift)
Open Docker Desktop or use the Docker CLI to manually stop or delete one of the containers provisioned by Terraform (e.g., frontend_node_dev). This simulates a rogue admin making changes outside of your IaC pipeline.

## Step 3: Catch the Drift
Run the verification script again:

```Bash
python verify.py --env dev
```

#### Expected Output: 

The Python SDK will instantly recognize that the live daemon state no longer matches the JSON architecture config. It will output 🚨 INFRASTRUCTURE DRIFT DETECTED 🚨, exit with a failure code, and generate a detailed audit artifact in your reports/ folder. To resolve this, simply re-run python deploy.py --env dev to allow Terraform to automatically restore the missing infrastructure.
