from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
import json

from telemetry import MLOpsTelemetryHandler
import uuid

import os

# --- 1. Define the Enterprise Tools ---
# The @tool decorator tells LangChain to extract the function name, 
# arguments, and docstring to teach the LLM how to use it.

@tool
def fetch_github_issue(issue_number: int) -> str:
    """Fetches the details and description of a specific GitHub issue."""
    print(f"  [Tool Execution] 🛠️ Fetching Issue #{issue_number}...")
    # Mocking an API response for local testing
    issues = {
        42: "The GKE production cluster is rejecting our terraform apply. Error: VPC-SC violation on subnet-a.",
        43: "Update the README to include local Docker instructions."
    }
    return issues.get(issue_number, "Issue not found.")

@tool
def query_infrastructure_codebase(search_term: str) -> str:
    """Searches the local infrastructure codebase for specific Terraform or Kubernetes configurations."""
    print(f"  [Tool Execution] 🛠️ Searching codebase for: '{search_term}'...")
    # Mocking a code search
    if "VPC-SC" in search_term or "subnet-a" in search_term:
        return """
        resource "google_compute_subnetwork" "subnet-a" {
          name          = "enterprise-subnet-a"
          network       = google_compute_network.vpc_network.id
          # SECURITY FLAG: Missing private Google access enforcement
        }
        """
    return "No relevant code found."

@tool
def draft_pull_request(repo: str, branch: str, fix_description: str) -> str:
    """Drafts a GitHub Pull Request with the proposed infrastructure fix."""
    print(f"  [Tool Execution] 🛠️ Drafting PR to {repo} on branch {branch}...")
    print(f"  [PR Content] {fix_description}")
    return f"Success: PR drafted for {repo}/{branch}"

# --- 2. Initialize the AI Agent ---
def run_autonomous_agent(user_prompt: str):
    print("🚀 Initializing Autonomous Infrastructure Agent...\n")

    # 1. Generate a unique Trace ID for this specific run
    run_trace_id = f"trace-{uuid.uuid4().hex[:8]}"
    telemetry = MLOpsTelemetryHandler(trace_id=run_trace_id)

    # PLATFORM ENGINEER FIX: Route traffic out of the pod to the Windows host
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

    # 2. Attach the telemetry handler to the LLM via the 'callbacks' array
    llm = ChatOllama(
        model="llama3.1",
        base_url=ollama_url,
        #base_url="http://localhost:11434",
        temperature=0,
        callbacks=[telemetry] # <--- THE WIRETAP IS NOW ACTIVE
    )  
        
    # Bind the tools to the LLM so it knows they exist
    tools = [fetch_github_issue, query_infrastructure_codebase, draft_pull_request]
    llm_with_tools = llm.bind_tools(tools)
    
    # Set the Agent's system prompt with strict sequential guardrails
    system_prompt = SystemMessage(content="""
    You are an automated Enterprise Infrastructure AI Agent.
    
    You MUST follow this exact sequence when resolving user requests:
    1. STEP 1: Always call 'fetch_github_issue' FIRST to retrieve the issue details.
    2. STEP 2: Analyze the issue description. Identify key keywords, resource names, or error codes (e.g., 'VPC-SC', 'subnet-a').
    3. STEP 3: Call 'query_infrastructure_codebase' using those specific keywords from Step 2 to locate the problematic code.
    4. STEP 4: Only after completing Steps 1-3, call 'draft_pull_request' with a clear description of the fix based on the code you found.

    Do NOT call 'draft_pull_request' until you have retrieved the issue and queried the codebase!
    """)
    
    messages = [system_prompt, HumanMessage(content=user_prompt)]
    
    print(f"❓ Trigger: {user_prompt}\n")
    print("🤖 Agent reasoning loop started...")

    # First Pass: The LLM decides which tool to call
    ai_msg = llm_with_tools.invoke(messages)
    
    # Loop through the tools the LLM requested to run
    if ai_msg.tool_calls:
        messages.append(ai_msg) # Save the AI's request to the chat history
        
        for tool_call in ai_msg.tool_calls:
            # Match the requested tool by name and execute it
            selected_tool = {"fetch_github_issue": fetch_github_issue, 
                             "query_infrastructure_codebase": query_infrastructure_codebase, 
                             "draft_pull_request": draft_pull_request}[tool_call["name"].lower()]
            
            tool_output = selected_tool.invoke(tool_call["args"])
            
            # Send the tool's output back to the LLM as a ToolMessage
            messages.append({"role": "tool", "content": str(tool_output), "tool_call_id": tool_call["id"]})
            
        # Second Pass: The LLM reads the tool output and drafts the final response/action
        final_response = llm_with_tools.invoke(messages)
        print(f"\n✨ Final Agent Action:\n{final_response.content}")
    else:
        print(f"\n✨ Agent Response (No tools needed):\n{ai_msg.content}")

if __name__ == "__main__":
    run_autonomous_agent("Please investigate and resolve GitHub Issue #42 in the enterprise-cloud repo.")

    # PLATFORM ENGINEER FIX: Prevent container exit in Kubernetes Deployment
    #print("Agent task execution completed. Keeping container alive...")
    #while True:
        #time.sleep(3600)