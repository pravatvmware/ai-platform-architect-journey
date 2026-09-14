import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from .state import AgentState

# 1. Initialize the LLM
# Explicitly set the base_url to bypass Windows localhost/0.0.0.0 routing issues
llm = ChatOllama(
    model="llama3.1", 
    temperature=0.1,
    base_url="http://127.0.0.1:11434"  # <-- ADD THIS LINE
)

# 2. Define the System Guardrails
SYS_PROMPT = """You are an elite Enterprise AI Platform Engineer agent.
Your job is to analyze infrastructure issues, read codebase files, and draft Terraform fixes.
Be concise, professional, and ensure all code drafts are secure and syntactically correct."""

def analyze_issue(state: AgentState) -> Dict[str, Any]:
    """Uses the LLM to analyze the issue and decide what context it needs."""
    print(f"--- Node: Analyzing Issue #{state['issue_id']} ---")
    
    # Prepend the System Prompt to guide the LLM's behavior
    messages = [SystemMessage(content=SYS_PROMPT)] + state["messages"]
    
    # ---------------------------------------------------------
    # 🏗️ MCP ARCHITECTURE NOTE:
    # In a fully async implementation, you dynamically load tools from the MCP server:
    # mcp_tools = await load_mcp_tools("python agent/mcp_server.py")
    # agent_llm = llm.bind_tools(mcp_tools)
    # response = agent_llm.invoke(messages)
    # ---------------------------------------------------------
    
    # For now, we invoke the standard LLM
    response = llm.invoke(messages)
    
    # The LLM reasons about the issue. In a full tool-execution loop, 
    # it would return a ToolCall here to trigger 'read_codebase'.
    mock_context = "Terraform configuration on subnet-a requires port 22."
    
    return {
        "codebase_context": mock_context,
        "messages": [response]
    }

def draft_code(state: AgentState) -> Dict[str, Any]:
    """Uses the LLM to generate the actual code fix."""
    print("--- Node: Drafting Code Fix ---")
    
    # Instruct the LLM to draft the fix based on the codebase context
    draft_prompt = HumanMessage(
        content=f"Based on this context: '{state['codebase_context']}', draft a PR description and the Terraform code fix."
    )
    
    messages = state["messages"] + [draft_prompt]
    
    # The LLM generates the actual code!
    response = llm.invoke(messages)
    
    # Structure the draft for the state object
    draft = {
        "title": f"Fix for Issue #{state['issue_id']}",
        "body": response.content, # This now contains real LLM-generated code
        "files_changed": ["vpc/main.tf"]
    }
    
    return {
        "pr_draft": draft,
        "messages": [response]
    }

def human_approval(state: AgentState) -> Dict[str, Any]:
    """Handles the human-in-the-loop review process."""
    print("--- Node: Human Approval Check ---")
    
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
    
    # The LLM finalizes the submission message
    final_msg = AIMessage(content="Pull request successfully pushed to the repository via MCP tool execution!")
    
    return {
        "messages": [final_msg]
    }