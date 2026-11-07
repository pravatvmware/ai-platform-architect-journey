---
layout: default
title: Phase 1 - Core Orchestrator
parent: 7. Project 5 - Python & Terraform Automation
nav_order: 1
---

# Phase 1: The Core Orchestrator
{: .no_toc }

This phase establishes the foundational Python automation engine. It uses the `subprocess` module to programmatically execute Terraform commands, capturing logs, handling errors, and exporting the execution plan for future validation, all without incurring cloud costs by utilizing local Docker infrastructure.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Directory Structure

Set up the project repository with the following structure before adding the code:

```text
project-5/
├── deploy.py
├── .gitignore
└── infrastructure/
    └── main.tf
```

## 1. Local Infrastructure Configuration
Save this as infrastructure/main.tf. This configuration uses the kreuzwerker/docker provider to simulate cloud provisioning on your local machine by pulling an NGINX image and deploying it as a container.

## 2. Python Orchestration Script
Save this as deploy.py in the root directory. This script wraps Terraform execution, streams the output directly to the terminal, handles failures, and exports the binary tfplan into a readable tfplan.json for Phase 3 policy scanning.

## 3. Execution & Verification
Ensure Docker Desktop is running.

Open your terminal in the project-5 root directory.

Run the orchestration script:

``` bash
python deploy.py
```
Verify Deployment: Navigate to http://localhost:8080 in your web browser to see the running NGINX welcome page, confirming the Python script successfully drove the Terraform deployment.
