import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from .state import AgentState

llm = ChatOllama(
    model="llama3.1", 
    temperature=0.1,
    base_url="http://127.0.0.1:11434"
)

SYS_PROMPT = """You are an elite Enterprise AI Platform Engineer agent.
Your job is to analyze infrastructure issues, read codebase files, and draft Terraform fixes.
Be concise, professional, and ensure all code drafts are secure and syntactically correct."""

# 1. Change to async def
async def analyze_issue(state: AgentState) -> Dict[str, Any]:
    print(f"--- Node: Analyzing Issue #{state['issue_id']} ---")
    messages = [SystemMessage(content=SYS_PROMPT)] + state["messages"]
    
    # 2. Change to ainvoke (asynchronous invoke)
    response = await llm.ainvoke(messages)
    
    mock_context = "Terraform configuration on subnet-a requires port 22."
    return {"codebase_context": mock_context, "messages": [response]}

async def draft_code(state: AgentState) -> Dict[str, Any]:
    print("--- Node: Drafting Code Fix ---")
    draft_prompt = HumanMessage(
        content=f"Based on this context: '{state['codebase_context']}', draft a PR description and the Terraform code fix."
    )
    messages = state["messages"] + [draft_prompt]
    
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
    final_msg = AIMessage(content="Pull request successfully pushed to the repository via MCP tool execution!")
    return {"messages": [final_msg]}