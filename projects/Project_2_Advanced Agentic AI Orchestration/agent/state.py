from typing import TypedDict, Annotated, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Input parameters
    issue_id: int
    issue_description: str
    
    # Working memory
    codebase_context: str
    pr_draft: Dict[str, Any]
    human_feedback: str
    
    # Conversation history (appends automatically)
    messages: Annotated[list[BaseMessage], add_messages]