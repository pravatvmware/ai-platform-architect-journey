---
layout: default
title: Phase 2 - Dynamic Generation
parent: 7. Project 5 - Python & Terraform Automation
nav_order: 2
---

# Phase 2: Dynamic Infrastructure Generation
{: .no_toc }

This phase transitions the framework from executing hardcoded Terraform files to programmatically generating infrastructure. By integrating Python's **Jinja2** templating engine, the automation pipeline can read standard JSON configuration files and dynamically render multi-tiered `.tf` files right before execution.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

Before starting, install the Jinja2 templating library in your Python environment:

```bash
pip install jinja2
```

## Directory Structure
Update your project directory to include the templates folder and the config.json file. The infrastructure/main.tf file is now deleted, as it will be generated automatically.

1. The Configuration Payload
Save this as config.json in your root directory. This declarative file represents the desired state of the infrastructure.

2. The Jinja2 Template
Save this as templates/main.tf.j2. It acts as the blueprint. The framework loops over the containers array from the JSON configuration to stamp out multiple dynamic resources.

3. The Updated Orchestrator
Replace your deploy.py with this updated engine. It introduces the generate_infrastructure() function to bridge the JSON payload and the Jinja2 template.

4. Execution & Verification
Run the Python pipeline:

```Bash
python deploy.py
```

### Verification:

Check the infrastructure folder; you will see a newly generated main.tf file containing the two NGINX containers defined in the JSON.

Open Docker Desktop or your browser (http://localhost:8081 and http://localhost:8082) to confirm both containers are live.

