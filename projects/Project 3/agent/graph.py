from typing import Annotated, Literal, Sequence, TypedDict
import operator
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from pydantic import BaseModel

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
        "- If the issue is fully resolved and the PR is submitted, route to FINISH."
    )
    
    # Force the LLM to output ONLY the routing decision
    supervisor_chain = llm.with_structured_output(Route)
    
    # Prepend the system instructions to the running conversation history
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    
    # Execute the routing decision
    response = supervisor_chain.invoke(messages)
    
    print(f"\n[Supervisor] Delegating task to: {response.next}")
    return {"next": response.next}