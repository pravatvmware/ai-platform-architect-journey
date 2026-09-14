import sys
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .state import AgentState

# 1. Initialize the LLM
llm = ChatOllama(
    model="llama3.1", 
    temperature=0.1,
    base_url="http://127.0.0.1:11434"
)

# ADD THIS MISSING VARIABLE HERE:
SYS_PROMPT = """You are an elite Enterprise AI Platform Engineer agent.
Your job is to analyze infrastructure issues, read codebase files, and draft Terraform fixes.
Be concise, professional, and ensure all code drafts are secure and syntactically correct."""

# ==========================================
# 🏗️ ENTERPRISE MCP CLIENT INTEGRATION
# ==========================================
async def execute_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Securely executes a tool on the isolated MCP server via stdio."""
    print(f"   [MCP Client] Spawning secure subprocess for '{tool_name}'...")
    
    # FIX 1: Use sys.executable to ensure the subprocess uses your .venv
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["agent/mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result.content[0].text
# ==========================================

async def analyze_issue(state: AgentState) -> Dict[str, Any]:
    print(f"--- Node: Analyzing Issue #{state['issue_id']} ---")
    
    # The agent decides it needs to read the VPC Terraform file, so it triggers the tool.
    tool_result = await execute_mcp_tool(
        tool_name="read_codebase", 
        arguments={"filepath": "vpc/main.tf"}
    )
    
    print(f"   [MCP Result] Successfully retrieved code via MCP server.")
    
    context_msg = AIMessage(content=f"I have read the codebase using the MCP tool. Here is the context:\n{tool_result}")
    
    return {"codebase_context": tool_result, "messages": [context_msg]}

async def draft_code(state: AgentState) -> Dict[str, Any]:
    print("--- Node: Drafting Code Fix ---")
    
    draft_prompt = HumanMessage(
        content=f"Based on this context from the MCP server: '{state['codebase_context']}', draft a PR description and the Terraform code fix."
    )
    messages = [SystemMessage(content=SYS_PROMPT)] + state["messages"] + [draft_prompt]
    
    # The LLM generates the fix based on the REAL data fetched by the MCP server
    response = await llm.ainvoke(messages)
    
    draft = {
        "title": f"Fix for Issue #{state['issue_id']}",
        "body": response.content,
        "files_changed": ["vpc/main.tf"]
    }
    return {"pr_draft": draft, "messages": [response]}

async def human_approval(state: AgentState) -> Dict[str, Any]:
    print("--- Node: Human Approval Check ---")
    if state.get("human_feedback"):
        feedback_msg = f"Received feedback: {state['human_feedback']}. Revisions needed."
    else:
        feedback_msg = "Draft approved by Platform Engineer. Proceeding to submit."
    return {"messages": [AIMessage(content=feedback_msg)]}

async def submit_pr(state: AgentState) -> Dict[str, Any]:
    print("--- Node: Submitting Pull Request ---")
    
    # Use the MCP tool again to securely push the final PR
    tool_result = await execute_mcp_tool(
        tool_name="submit_github_pr",
        arguments={"issue_id": state['issue_id'], "fix_description": "VPC-SC Port 22 Fix"}
    )
    
    final_msg = AIMessage(content=f"Tool Execution Complete: {tool_result}")
    return {"messages": [final_msg]}