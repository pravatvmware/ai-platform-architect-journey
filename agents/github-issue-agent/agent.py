from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
import json

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
    
    # Initialize the specific model capable of tool calling
    llm = ChatOllama(
        model="llama3.1",
        base_url="http://localhost:11434",
        temperature=0
    )
    
    # Bind the tools to the LLM so it knows they exist
    tools = [fetch_github_issue, query_infrastructure_codebase, draft_pull_request]
    llm_with_tools = llm.bind_tools(tools)
    
    # Set the Agent's system prompt to enforce architectural guardrails
    system_prompt = SystemMessage(content="""
    You are an automated Enterprise Infrastructure AI Agent. 
    Your job is to triage incoming issues, search the codebase for the root cause, 
    and draft a pull request to fix it. Always use your tools to gather information before acting.
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