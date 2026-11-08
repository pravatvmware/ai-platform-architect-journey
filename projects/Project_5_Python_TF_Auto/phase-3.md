---
layout: default
title: Phase 3 - Enterprise Security
parent: 7. Project 5 - Python & Terraform Automation
nav_order: 3
---

# Phase 3: Enterprise Architecture & Security
{: .no_toc }

This phase elevates the framework to an enterprise-grade standard. It introduces **Policy-as-Code** (using Checkov) to halt insecure deployments, **Terraform Workspaces** to isolate state files across environments (Dev/UAT/Prod), and **Artifact Generation** to publish a consolidated Markdown execution report after every run.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

Install the Checkov policy-as-code scanner in your Python environment:

```bash
pip install checkov jinja2
```

## Directory Structure
Update your project directory to support multiple environments and execution reports.

```
project-5/
├── deploy.py
├── configs/
│   ├── dev.json
│   └── prod.json
├── templates/
│   └── main.tf.j2
├── reports/          <-- (Generated pipeline artifacts)
└── infrastructure/   <-- (Generated .tf files and workspace state)
```

1. Environment Configurations
Instead of a single config.json, create environment-specific configurations inside the configs/ folder.

configs/dev.json

configs/prod.json

2. The Enterprise Gate Orchestrator
Replace deploy.py with this finalized Phase 3 engine.

Key features introduced in this script:

setup_workspace(): Switches Terraform workspaces based on the --env flag, isolating state files just like an S3 backend.

run_security_scan(): Uses shutil.which to reliably locate Checkov, executing a --soft-fail scan to log warnings without breaking local Docker tests.

publish_report(): Extracts the readable Terraform plan and Checkov scan, publishing a timestamped .md artifact for auditing.

3. Execution & Verification
Run the pipeline by passing the --env flag targeting your desired environment config.

```Python
python deploy.py --env dev
```

### Expected Output
The framework will create (or switch to) the dev Terraform workspace.

Checkov will execute a soft-fail scan on the dynamic JSON plan and print warnings to the terminal.

A timestamped artifact will be saved in the reports/ folder (e.g., dev_execution_report_2026-11-08_12-00-00.md).

Terraform will apply the Dev infrastructure safely to your local Docker daemon.

