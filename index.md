
**Bridging the gap between secure, scalable cloud infrastructure and Agentic AI.**

---

## 🏗️ About Me

With 20 years of experience architecting secure, automated, and highly scalable cloud infrastructure, I am applying enterprise systems-thinking to the AI frontier. 

Most AI development happens in isolated labs. My focus is operationalizing AI: designing the secure platforms, robust Retrieval-Augmented Generation (RAG) pipelines, and Agentic frameworks required to run AI safely within the enterprise. I specialize in infrastructure as code, Kubernetes, and translating complex AI workflows into governed, scalable cloud realities.

[Connect on LinkedIn](#) | [View GitHub Repositories](https://github.com/pravatvmware)

---

## 🚀 Active Projects & Architecture

This portfolio documents my hands-on transition and active engineering projects, building enterprise-grade AI platforms from the ground up.

### 1. Local-First Enterprise RAG Pipeline (In Progress)
*Designing a secure, zero-cost local environment mimicking GCP enterprise architecture.*
* **Architecture:** Kubernetes (Kind), PostgreSQL + pgvector, Ollama (Local LLMs).
* **Focus:** Deploying a secure data ingestion and retrieval pipeline entirely on local infrastructure, proving data privacy and system isolation before cloud deployment.
* [View Architecture Diagrams](./architecture-diagrams/local-rag-architecture.md) | [View Infrastructure Code](./infrastructure/local-k8s/)

### 2. Autonomous GitHub Issue Triage Agent (Planned)
*Orchestrating AI agents to automate platform engineering workflows.*
* **Architecture:** Python, LangChain, Function Calling, API Webhooks.
* **Focus:** Building an autonomous agent that reads incoming infrastructure issues, queries the repository codebase for context, and proposes terraform/code fixes via pull request. 
* [View Agent Code](./agents/github-issue-agent/)

---

## 📚 Technical Philosophy

1. **Governance First:** AI without guardrails is a liability. Infrastructure must enforce data perimeters (VPC-SC) and strict IAM least-privilege.
2. **Measurable Automation:** Avoid reactive operations. Build systems that self-heal, auto-scale, and resolve their own issues.
3. **Architecture over Hype:** Focus on the underlying plumbing—vector databases, compute scaling, and secure networking—that makes AI actually useful to a business.

---
*Documenting the journey from Cloud Architect to Enterprise AI Platform Architect.*

## 3. Enterprise Guardrails & Security (Phase 4)

*Transitioning local AI prototypes into a hardened GCP cloud architecture.*

**Phase 4 Architectural Blueprint**

```text
                     +-------------------------------------------------------+
                     |             GCP VPC Service Control Perimeter         |
                     |                                                       |
  [ Developer / ] -- | --> [ Identity-Aware Proxy ]                          |
  [ CI/CD Pipeline]  |                 |                                     |
                     |                 v                                     |
                     |     [ Private GKE Cluster ]                           |
                     |     (Agent Runtime Layer)                             |
                     |         |               |                             |
                     |  Workload Identity      | Private Google Access       |
                     |         |               v                             |
                     |         +-----> [ Vertex AI APIs ]                    |
                     |         |       (Embedding / LLM Inference)           |
                     |         |                                             |
                     |         +-----> [ AlloyDB / Cloud SQL (pgvector) ]    |
                     |                 (Encrypted Vector Store - CMEK)       |
                     +-------------------------------------------------------+
                                               |
                                               v
                                   [ Cloud Audit Logs & Trace ]
                                     (MLOps Telemetry Layer)
```                             

---

## 🎯 Concluding the Architectural Journey: From Prototype to Enterprise

This portfolio demonstrates the complete lifecycle of operationalizing Agentic AI. By systematically moving through four distinct engineering phases, I bridged the gap between experimental LLM scripts and a governed, scalable, enterprise-grade cloud architecture.

### The 4-Phase Engineering Blueprint:

*   **Phase 1 & 2: The Data Foundation (Local RAG Pipeline)**
    *   Designed a secure, air-gapped local environment to simulate enterprise data privacy.
    *   Provisioned a containerized PostgreSQL database supercharged with the `pgvector` extension.
    *   Deployed Ollama to serve local embedding models (`nomic-embed-text`) and inference models (`llama3`), creating a zero-cost, private Retrieval-Augmented Generation (RAG) pipeline.
*   **Phase 3: Autonomous Orchestration (Agentic Frameworks)**
    *   Upgraded the compute layer to utilize tool-calling models (`llama3.1`).
    *   Engineered a LangChain execution loop enforcing the strict **ReAct (Reason + Act)** pattern.
    *   Built an autonomous AI Agent that dynamically intercepts GitHub webhooks, queries Terraform infrastructure repositories for context, and drafts pull requests to resolve network configuration errors without human intervention.
*   **Phase 4: Security, Governance & MLOps (GCP Productionization)**
    *   **Observability:** Engineered custom Python telemetry interceptors to stream agent reasoning traces, tool latency, and token consumption directly to Google Cloud Logging.
    *   **Perimeter Security:** Architected Infrastructure as Code (Terraform) to map out GCP VPC Service Controls (VPC-SC), ring-fencing Vertex AI and AlloyDB to prevent data exfiltration.
    *   **Zero-Trust Identity:** Replaced highly vulnerable static Service Account JSON keys with Workload Identity Federation, dynamically binding GKE Kubernetes Service Accounts (KSA) to Google IAM roles for short-lived, secure access tokens.

**Final Takeaway:** 
AI without guardrails is a liability. By treating AI models with the same rigorous networking, IAM, and observability standards as traditional enterprise databases, we can safely unlock the power of autonomous engineering platforms.