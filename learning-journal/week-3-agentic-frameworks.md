# Week 3: Agentic Frameworks and Tool Orchestration

**Goal:** Transition from passive RAG systems to autonomous, action-taking AI agents using function calling.

## 🛠️ Architecture & Components Built

To orchestrate complex platform engineering workflows, I built the foundation for an **Autonomous GitHub Issue Agent**.

1. **Tool Definition (The "Hands"):**
   * Engineered explicit Python functions (`@tool`) mapped to typical DevOps workflows: fetching issue tickets, querying Infrastructure as Code (IaC) repositories, and drafting Pull Requests.
   * Utilized strict type-hinting and docstrings, which serve as the API contract for the LLM to understand how and when to invoke system operations.

2. **Agent Orchestration (The "Brain"):**
   * Transitioned to `llama3.1` (via Ollama) to leverage native tool-calling capabilities.
   * Implemented the LangChain orchestration loop: 
     - **Observation:** Agent receives a webhook/prompt.
     - **Reasoning:** Agent parses the request and outputs a structured JSON tool call.
     - **Action:** Python intercepts the JSON, executes the local system function, and feeds the state back to the LLM.
     - **Resolution:** Agent synthesizes the tool outputs into a final architectural action.

## 💡 Architect Key Takeaway
By wrapping standard automation scripts inside an Agentic loop, infrastructure platforms can shift from reactive alerting (sending an engineer a ticket) to proactive resolution (the agent parsing the terraform error, finding the missing VPC-SC configuration, and drafting the PR autonomously).

---
*Next Phase: Preparing the architecture for GCP deployment and enforcing Enterprise Guardrails.*