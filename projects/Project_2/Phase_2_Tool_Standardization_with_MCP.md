## 🛠️ Phase 2 Execution (Part 1): LLM Integration & Asynchronous Architecture

In the first half of Phase 2, we replaced the mocked reasoning engine with a live, local LLM (Ollama) and refactored the entire LangGraph architecture to be fully asynchronous. This is a prerequisite for executing secure, non-blocking subprocesses via the Model Context Protocol (MCP).

### 🧠 Key Architectural Milestones

1. **Tool Isolation (FastMCP):**
   * Scaffolded an independent microservice (`agent/mcp_server.py`) using the `FastMCP` SDK.
   * Encapsulated infrastructure tools (`read_codebase`, `submit_github_pr`) inside this server. This ensures the LangGraph agent never accesses the local file system or external APIs directly, adhering to strict zero-trust boundaries.

2. **Local LLM Integration:**
   * Replaced hardcoded text generation with `ChatOllama` (Llama 3.1) via LangChain.
   * Injected a strict `SystemMessage` to enforce the agent's persona as an Enterprise AI Platform Engineer.
   * **Network Routing Challenge:** Encountered a Windows socket error (`[WinError 10049]`) caused by previous Docker `OLLAMA_HOST=0.0.0.0` bindings. Resolved this by explicitly defining the LLM's `base_url="http://127.0.0.1:11434"` to ensure reliable localhost routing outside of containers.

3. **Asynchronous Orchestration:**
   * **The Problem:** Standard synchronous Python functions (`def`) block the FastAPI event loop. If the agent had to wait 10 seconds for a tool to execute on the MCP server, the entire web server would freeze.
   * **The Solution:** Upgraded the LangGraph nodes to use `async def` and `await llm.ainvoke()`. 
   * Updated the FastAPI endpoint in `main.py` to `await agent_workflow.ainvoke()`, resulting in a highly scalable, non-blocking enterprise API.

---

### 📝 Code State Snapshot

**The Async Node Pattern (`agent/nodes.py`):**
```python
async def draft_code(state: AgentState) -> Dict[str, Any]:
    print("--- Node: Drafting Code Fix ---")
    
    draft_prompt = HumanMessage(
        content=f"Based on this context: '{state['codebase_context']}', draft a PR description and the Terraform code fix."
    )
    
    # Passing the full conversation history to the LLM
    messages = [SystemMessage(content=SYS_PROMPT)] + state["messages"] + [draft_prompt]
    
    # Asynchronously invoking the LLM so the web server doesn't block
    response = await llm.ainvoke(messages)
    
    draft = {
        "title": f"Fix for Issue #{state['issue_id']}",
        "body": response.content,
        "files_changed": ["vpc/main.tf"]
    }
    
    return {"pr_draft": draft, "messages": [response]}


### Execution Verification:
Successfully triggered the async FastAPI endpoint (POST /agent/issues/resolve). The local Llama 3.1 model successfully parsed the mocked codebase context and generated syntactically correct Terraform HCL code to resolve a VPC-SC violation.

🚀 What's Next: The Final MCP Client Integration
Currently, the LLM is reasoning asynchronously, but it is still relying on mocked data.

The final step is to use the official mcp Python SDK to build the execute_mcp_tool client. This will allow the async LangGraph nodes to securely spawn the mcp_server.py subprocess, dynamically execute the tool requests over standard I/O (stdio), and return real contextual data back to the LLM's reasoning engine.