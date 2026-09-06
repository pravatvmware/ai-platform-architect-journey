# 🏗️ Project 2: Advanced Agentic AI Orchestration

**Objective:** Evolve the foundational GitHub Issue Agent (from Project 1) into a stateful, multi-agent system. This project introduces cyclical workflows, persistent memory, standardized tool integrations, and human-in-the-loop approvals, ultimately wrapping the agent as an enterprise-grade API.

## Core Technologies
* **Orchestration:** LangGraph
* **Tool Standardization:** Model Context Protocol (MCP)
* **API Delivery:** FastAPI, Uvicorn
* **LLM Engine:** Local open-source models (via Ollama) / Gemini API

---

## 🗺️ Architectural Blueprint

### Phase 1: LangGraph State Machine
Transitioning from a linear execution script to a directed cyclic graph (DCG) to enable reasoning, iteration, and memory.
* **State Definition:** Implement a centralized state object to maintain conversation history, retrieved codebase context, and current issue details.
* **Node Construction:** Build isolated Python functions for specialized tasks:
  * `Analyze_Issue`
  * `Draft_Code_Fix`
  * `Human_Approval`
  * `Submit_Pull_Request`
* **Edge Routing:** Define conditional logic to wire nodes together (e.g., routing a rejected PR draft back to the coding node for revisions before proceeding).

### Phase 2: Tool Standardization with MCP
Decoupling the agent's core reasoning engine from its execution tools to enforce strict security boundaries and enterprise guardrails.
* **MCP Server:** Host the GitHub API and local file system tools within an isolated MCP server.
* **Client Integration:** Configure the LangGraph agent as an MCP client, allowing it to dynamically discover and execute tools without hardcoded logic.
* **Context Isolation:** Enforce security guardrails ensuring the agent only accesses explicitly permitted repositories and subnets.

### Phase 3: Enterprise API Delivery
Transforming the local Python script into a robust, deployable microservice.
* **FastAPI Wrapper:** Embed the compiled LangGraph application within a FastAPI service.
* **Asynchronous Endpoints:** Design non-blocking REST endpoints (e.g., `POST /agent/issues/{id}/resolve`) to allow external webhooks or user interfaces to trigger agentic workflows.

---

## 🚀 Execution Log
*(This section will be updated with commands, code snippets, and troubleshooting steps as the project progresses).*

* **Step 1:** Initializing the FastAPI project structure. [Pending]
* **Step 2:** ...