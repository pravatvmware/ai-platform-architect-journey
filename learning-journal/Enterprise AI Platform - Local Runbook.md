# 🛠️ Enterprise AI Platform - Local Runbook

This guide contains the step-by-step commands to provision, configure, and execute the local-first Enterprise AI infrastructure.

## Phase 2: RAG Pipeline (Data Ingestion & Inference)

### 1. Database Provisioning (`pgvector`)
We use Docker to host a local PostgreSQL instance supercharged with vector search capabilities, mimicking GCP AlloyDB.

**Start the Database:**
```powershell
# Navigate to the infrastructure folder
cd infrastructure/local-data

# Spin up the container (runs in detached mode)
docker-compose up -d
```

**Initialize the Vector Extension:**
*(Note: We use port `5433` and user `rag_admin` to avoid local Windows conflicts).*
```powershell
docker exec -it enterprise-vector-db psql -U rag_admin -d rag_database -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Troubleshooting Note (Resetting DB):**
If you ever need to wipe the database and start fresh, you must delete the persistent volume:
```powershell
docker-compose down -v
docker-compose up -d
```

### 2. AI Inference Engine Setup (Ollama)
Ollama acts as our local Vertex AI endpoint. We need two models for RAG: one for embedding (math) and one for generation (chat).

**Pull the Models:**
```powershell
# For turning text into 768-dimensional vectors
ollama pull nomic-embed-text

# For reading the context and answering the user
ollama pull llama3
```

### 3. Python Environment & Execution
Install the required libraries to connect Python to Postgres and Ollama.

**Install Dependencies:**
```powershell
# Navigate back to the project root
cd ../../ 
pip install psycopg2-binary requests pgvector
```

**Run the RAG Pipeline:**
```powershell
# 1. Ingest the text into the database
python agents/local-rag-pipeline/ingest.py

# 2. Ask a question and retrieve context
python agents/local-rag-pipeline/query.py
```

---

## Phase 3: Agentic Framework (Function Calling)

### 1. Upgrade the AI Engine
Standard models cannot execute tools reliably. We must pull a model fine-tuned for tool orchestration and Agentic reasoning.

**Pull the Agent Model:**
```powershell
ollama pull llama3.1
```

### 2. Python Environment Update
We introduce LangChain as the orchestration framework to bind Python functions to the LLM.

**Install Agent Dependencies:**
```powershell
pip install langchain-core langchain-ollama requests
```

### 3. Run the Autonomous Agent
Execute the agent that fetches GitHub issues, searches the codebase, and drafts PRs.

**Run the Agent:**
```powershell
python agents/github-issue-agent/agent.py
```

---

## 🏗️ Architectural Core Concepts (The "Why")

*   **IPv4 vs IPv6:** Always use `127.0.0.1` instead of `localhost` in your Python database connection strings (`DB_CONFIG`) on Windows to prevent Docker networking timeouts.
*   **Vector Distance (`<=>`):** In `query.py`, the SQL operator `<=>` calculates the Cosine Distance. This is the mathematical magic that finds relevant text without relying on exact keyword matches.
*   **The ReAct Pattern:** An agent must **Observe -> Reason -> Act**. If an agent skips steps (like drafting a PR before reading the issue), it is an architectural failure.
*   **Tool-Level Guardrails:** When smaller local models (like `llama3.1`) ignore the `SystemMessage`, you must hardcode strict operational guardrails directly into the Python `@tool` docstrings (e.g., *"CRITICAL: You MUST use this tool FIRST"*).