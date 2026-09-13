from typing import Dict, Any
from langchain_core.messages import AIMessage
from .state import AgentState

def analyze_issue(state: AgentState) -> Dict[str, Any]:
    """Analyzes the GitHub issue and retrieves codebase context."""
    print(f"--- Node: Analyzing Issue #{state['issue_id']} ---")
    
    # TODO: Connect MCP to fetch real repository data
    mock_context = "Found Terraform module: vpc-sc configuration on subnet-a requires port 22."
    
    return {
        "codebase_context": mock_context,
        "messages": [AIMessage(content="I have analyzed the issue and retrieved the codebase context.")]
    }

def draft_code(state: AgentState) -> Dict[str, Any]:
    """Drafts the code fix based on the codebase context."""
    print("--- Node: Drafting Code Fix ---")
    
    # TODO: Connect Ollama LLM to generate the actual fix
    draft = {
        "title": f"Fix for Issue #{state['issue_id']}",
        "body": "Updated VPC-SC to allow ingress on port 22.",
        "files_changed": ["vpc/main.tf"]
    }
    
    return {
        "pr_draft": draft,
        "messages": [AIMessage(content="I have drafted a pull request to fix the infrastructure issue.")]
    }

def human_approval(state: AgentState) -> Dict[str, Any]:
    """Handles the human-in-the-loop review process."""
    print("--- Node: Human Approval Check ---")
    
    # If the API provided feedback in the state, log it. Otherwise, assume approved.
    if state.get("human_feedback"):
        feedback_msg = f"Received feedback: {state['human_feedback']}. Revisions needed."
    else:
        feedback_msg = "Draft approved by Platform Engineer. Proceeding to submit."
        
    return {
        "messages": [AIMessage(content=feedback_msg)]
    }

def submit_pr(state: AgentState) -> Dict[str, Any]:
    """Submits the approved Pull Request back to GitHub."""
    print("--- Node: Submitting Pull Request ---")
    
    # TODO: Connect MCP to push the PR to GitHub
    return {
        "messages": [AIMessage(content="Pull request successfully submitted to the repository!")]
    }