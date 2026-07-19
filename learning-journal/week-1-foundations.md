# Week 1: Enterprise AI Architecture Foundations

**Date:** July 2026  
**Goal:** Transitioning from Cloud/DevOps Engineering to Enterprise AI Platform Architecture.

## 1. The Architectural Pivot
The industry is shifting from standard infrastructure automation to **Agentic AI**. My focus is not on training models, but on **operationalizing AI**: building the secure, scalable, and automated infrastructure that allows AI agents to reason, use tools, and access enterprise data securely.

## 2. AWS to GCP Conceptual Mapping for AI
To architect on GCP (the current leader in enterprise AI via Vertex AI), I mapped my existing AWS knowledge to GCP paradigms:

| Concept | AWS Paradigm | GCP Paradigm | Architect's View for AI |
| :--- | :--- | :--- | :--- |
| **Boundary** | AWS Account | GCP Project / Folder | Isolate Dev, Stage, and Prod AI environments into separate Projects. IAM permissions flow top-down. |
| **Compute** | EKS / ECS | GKE (Kubernetes Engine) | GKE is the workhorse for containerized AI agents. Cloud Run is ideal for serverless, event-driven AI tasks (scaling to zero). |
| **Security** | VPC Endpoints | VPC Service Controls | **Crucial:** VPC-SC creates a security perimeter preventing enterprise data exfiltration from AI models. |
| **Vector Data**| RDS (PostgreSQL) | AlloyDB / Cloud SQL | AlloyDB with `pgvector` stores the mathematical embeddings required for Retrieval-Augmented Generation (RAG). |
| **AI Platform**| SageMaker / Bedrock | Vertex AI | The command center for accessing Foundation Models (Gemini) and managing ML pipelines. |

## 3. The Local-First Architecture Strategy
To ensure data privacy and avoid unnecessary cloud costs during development, I am building the enterprise architecture locally first. This mimics the cloud environment perfectly:

* **Cloud Storage** $\rightarrow$ Local Volume Mounts (for raw document ingestion)
* **GKE / Cloud Run** $\rightarrow$ Kubernetes via `Kind` (Compute layer for LangChain/Python)
* **AlloyDB (Vector Search)** $\rightarrow$ PostgreSQL + `pgvector` via Docker
* **Vertex AI** $\rightarrow$ Ollama (Local LLM inference via REST API)

## 4. RAG Pipeline Architecture
I designed the conceptual architecture for a **Retrieval-Augmented Generation (RAG)** system, dividing it into two flows:
1. **Data Ingestion:** Reading local documents, chunking the text, generating embeddings via Ollama, and storing them in the pgvector database.
2. **Inference:** Converting a user's question into an embedding, performing a similarity search in the database, and sending the relevant context to the LLM to generate a grounded answer.

---
*Next Steps: Provisioning the local PostgreSQL + pgvector database via Docker Compose.*

## 5. Hands-on Local Platform Implementation (Completed)

To transition from pure architecture theory to concrete engineering, I successfully established the local data and inference infrastructure layers:

### Data Layer: PostgreSQL + pgvector
*   **Implementation:** Provisioned an enterprise-grade relational database running inside a Docker container via a custom `docker-compose.yml`.
*   **Persistence:** Configured a named volume (`pgvector_enterprise_data`) to map data onto local host storage, ensuring database state survives container lifecycles (simulating GCP persistent storage volumes).
*   **Vector Capability:** Executed the native database command to activate the `pgvector` database extension (`CREATE EXTENSION IF NOT EXISTS vector;`), transforming standard relational storage into a high-dimensional vector index space.

### Inference Layer: Ollama Engine
*   **Implementation:** Configured a local AI runtime engine to expose a standard REST API endpoint on port `11434`, successfully mirroring public cloud inference mechanics (Vertex AI APIs).
*   **Model Deployment:** Pulled the foundational text embedding model `nomic-embed-text` directly into the local environment.
*   **Verification:** Verified system integration using native PowerShell web requests (`Invoke-RestMethod`), successfully triggering the engine to transform unstructured text data into high-dimensional numerical arrays (embeddings).

---
*Next Steps: Building Phase 2: Writing the Python data ingestion script to parse local files, generate real embeddings via Ollama, and dynamically write them into the pgvector instance.*