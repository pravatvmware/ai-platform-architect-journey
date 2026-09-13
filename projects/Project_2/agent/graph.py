from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import analyze_issue, draft_code, human_approval, submit_pr

# 1. Initialize the StateGraph with our AgentState schema
workflow = StateGraph(AgentState)

# 2. Register all the nodes
workflow.add_node("analyze", analyze_issue)
workflow.add_node("draft", draft_code)
workflow.add_node("approve", human_approval)
workflow.add_node("submit", submit_pr)

# 3. Define the routing logic (Edges)
# Start -> Analyze -> Draft -> Approve
workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", "draft")
workflow.add_edge("draft", "approve")

# 4. Conditional Edge: Human-in-the-loop decision
def check_approval(state: AgentState) -> str:
    """Routes the graph based on human feedback."""
    # If the human provided feedback, send it back to the drafting node for revisions
    if state.get("human_feedback"):
        return "draft"
    # If no feedback (approved), proceed to submit
    return "submit"

workflow.add_conditional_edges(
    "approve",
    check_approval,
    {
        "draft": "draft",    # Route back for revisions
        "submit": "submit"   # Route forward to completion
    }
)

# 5. Finish the graph
workflow.add_edge("submit", END)

# 6. Compile the graph into an executable application
app = workflow.compile()