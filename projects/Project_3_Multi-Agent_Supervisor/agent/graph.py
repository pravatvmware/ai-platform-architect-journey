import os
from typing import Annotated, Literal, Sequence, TypedDict
import operator
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from pydantic import BaseModel

# 1. Force Python to ignore all VPNs/Proxies for local traffic
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

from langchain_ollama import ChatOllama

# 2. Initialize the Local LLM using 'localhost' instead of the IP
llm = ChatOllama(
    model="llama3.1", 
    temperature=0,
    base_url="http://localhost:11434" 
) 

# --- 1. The Multi-Agent State ---
class AgentState(TypedDict):
    # operator.add ensures new messages are appended to the history, not overwritten
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Tracks which sub-agent the supervisor delegates to next
    next: str

# --- 2. The Supervisor Routing Schema ---
class Route(BaseModel):
    """Decide which worker should act next based on the conversation history."""
    next: Literal["Infrastructure_Agent", "Deployment_Agent", "FINISH"]

# --- 3. The Supervisor Node ---
def supervisor_node(state: AgentState):
    system_prompt = (
        "You are an Enterprise DevOps Supervisor managing a team of two specialized AI agents:\n"
        "1. Infrastructure_Agent: Reads the codebase, analyzes Terraform, and writes fixes.\n"
        "2. Deployment_Agent: Takes drafted code and pushes it to GitHub as a Pull Request.\n\n"
        "Given the user request and the current conversation history, decide who should act next.\n"
        "- If code needs to be read or written, route to Infrastructure_Agent.\n"
        "- If code has been drafted but not pushed, route to Deployment_Agent.\n"
        "- If the Deployment_Agent confirms the PR is successfully submitted, you MUST route to FINISH."
    )
    
    # Force the LLM to output ONLY the routing decision
    supervisor_chain = llm.with_structured_output(Route)
    
    # Prepend the system instructions to the running conversation history
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Execute the routing decision
    response = supervisor_chain.invoke(messages)
    
    print(f"\n[Supervisor] Delegating task to: {response.next}")
    return {"next": response.next}

from langgraph.graph import StateGraph, END

# --- 4. The Sub-Agents (The Workers) ---

def infrastructure_node(state: AgentState):
    """Infrastructure Agent: Analyzes code and drafts fixes."""
    system_prompt = (
        "You are the Infrastructure Agent. You specialize in Terraform and DevOps.\n"
        "Your job is to read the codebase and draft the necessary code fixes.\n"
        "Once you have drafted the code, summarize your work so the Deployment Agent can push it."
    )
    
    # FUTURE STEP: Here is where we will isolate tools! 
    # Example: agent = llm.bind_tools([read_codebase_tool])
    agent = llm 
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = agent.invoke(messages)
    
    # We return the response as a list so operator.add appends it to the state history
    print(f"\n[Infrastructure Agent] Task executed.")
    return {"messages": [response]}


def deployment_node(state: AgentState):
    """Deployment Agent: Submits the PR."""
    system_prompt = (
        "You are the Deployment Agent. You manage GitHub Pull Requests.\n"
        "Take the drafted code from the conversation history and push it to GitHub.\n"
        "You MUST explicitly reply with exactly this sentence: 'SUCCESS: The Pull Request has been submitted and the issue is fully resolved.' Do not add any other text."
    )
    
    # FUTURE STEP: Here is where we will isolate tools!
    # Example: agent = llm.bind_tools([submit_github_pr_tool])
    agent = llm 
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = agent.invoke(messages)
    
    print(f"\n[Deployment Agent] Task executed.")
    return {"messages": [response]}


# --- 5. Building the Multi-Agent Graph ---

workflow = StateGraph(AgentState)

# Add the three entities as nodes
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Infrastructure_Agent", infrastructure_node)
workflow.add_node("Deployment_Agent", deployment_node)

# The Supervisor decides who goes next using a Conditional Edge
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"], # Read the routing decision from the state
    {
        "Infrastructure_Agent": "Infrastructure_Agent",
        "Deployment_Agent": "Deployment_Agent",
        "FINISH": END
    }
)

# CRITICAL: Once a sub-agent finishes its task, it MUST report back to the Supervisor
workflow.add_edge("Infrastructure_Agent", "Supervisor")
workflow.add_edge("Deployment_Agent", "Supervisor")

# The graph always starts with the Supervisor evaluating the request
workflow.set_entry_point("Supervisor")

# Compile the graph
app = workflow.compile()