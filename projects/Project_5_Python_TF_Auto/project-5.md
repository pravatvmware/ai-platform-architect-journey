---
layout: default
title: 7. Project 5 - Python & Terraform Automation
nav_order: 8
has_children: false
---

# Project 5: Local-First Infrastructure Automation Framework (Python + Terraform)
{: .no_toc }

*Simulating enterprise-grade cloud automation and AI-assisted deployment entirely on local infrastructure (Zero Cloud Billing).*

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## 🎯 Project Overview

Most enterprise cloud automation relies heavily on costly cloud provider services for testing and validation. This project focuses on building a robust, production-ready Infrastructure as Code (IaC) automation framework using **Python** and **Terraform**, executed entirely locally using the `kreuzwerker/docker` provider. 

By mapping cloud concepts to local Docker resources (e.g., VNets mapped to Docker Networks, VMs to Docker Containers), this framework allows for the rapid, cost-free development of an automation engine that can later be pointed to Azure or GCP simply by swapping the Terraform provider.

**Core Tech Stack:** Python, Terraform, Docker, Jinja2, Checkov, LangGraph.

---

## 🚀 The 5-Phase Engineering Blueprint

This project follows a phased approach, evolving from a basic Python execution wrapper to a fully autonomous, AI-driven deployment agent.

### Phase 1: The Core Orchestrator (Current)
*Executing and managing Terraform state via Python.*
- **Architecture:** Python `subprocess` module, Pydantic for validation, and standard logging.
- **Focus:** Building a robust CLI tool that safely triggers `terraform init`, `plan`, and `apply` against local Docker infrastructure.
- **Outcome:** A controlled local environment where Python directly orchestrates Terraform resource creation without manual CLI intervention.

### Phase 2: Dynamic Infrastructure Generation
*Moving from hardcoded HCL to programmatic templates.*
- **Architecture:** Python + Jinja2 templating engine.
- **Focus:** Reading JSON/YAML architecture definitions and dynamically generating multi-tiered `main.tf` and `variables.tf` files prior to deployment.
- **Outcome:** A scalable engine capable of stamping out complex environments (networks, subnets, and compute) based on simple configuration files.

### Phase 3: Enterprise Architecture & Security
*Enforcing policy-as-code and remote state simulation.*
- **Architecture:** Checkov / Open Policy Agent (OPA), MinIO (Local State).
- **Focus:** Integrating security scanning directly into the Python pipeline. If a `terraform plan` output violates predefined security policies (e.g., exposed ports), the Python engine halts the deployment.
- **Outcome:** A secure, enterprise-grade pipeline mimicking Dev/UAT/Prod environments.

### Phase 4: Verification & Drift Detection
*Closing the loop between intended state and actual state.*
- **Architecture:** Python `docker` SDK.
- **Focus:** Using the Python SDK to independently query the local Docker daemon post-deployment, verifying that resources exist exactly as defined in the configuration files.
- **Outcome:** Automated drift detection that alerts if manual changes occur outside the Terraform pipeline.

### Phase 5: AI-Assisted Agentic Automation
*Natural language infrastructure requests and remediation.*
- **Architecture:** Python, LangGraph, Local LLMs (Ollama).
- **Focus:** Building a multi-agent supervisor system where an Architect Agent translates natural language into JSON configs, a Reviewer Agent validates the Checkov security scans, and a Deployer Agent executes the Terraform code.
- **Outcome:** A conversational infrastructure deployment engine.

---

## 🛠️ Current Status: Phase 1 Implementation

Currently initiating Phase 1. The immediate focus is establishing the Python wrapper and successfully deploying a local Docker container using Terraform via Python `subprocess`.

[View Infrastructure Code on GitHub](#) *(Link to be added once repository is pushed)*