from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from langchain_core.messages import HumanMessage

# Import our compiled LangGraph application
from agent.graph import app as agent_workflow

# Initialize the Enterprise API
app = FastAPI(title="Enterprise Agentic API", version="1.0.0")

# Define the expected JSON payload using Pydantic
class IssueRequest(BaseModel):
    issue_id: int
    issue_description: str

@app.get("/health")
async def health_check():
    return {"status": "Agent API is healthy and listening"}

@app.post("/agent/issues/resolve")
async def resolve_issue(request: IssueRequest):
    print(f"\n--- API Triggered: Resolving Issue #{request.issue_id} ---")
    
    # 1. Initialize the starting state for the graph
    initial_state = {
        "issue_id": request.issue_id,
        "issue_description": request.issue_description,
        # Kick off the conversation history with the user's prompt
        "messages": [HumanMessage(content=f"Please resolve this issue: {request.issue_description}")]
    }
    
    # 2. Execute the LangGraph workflow
    # Note: .invoke() runs the entire graph from START to END
    # 2. Execute the LangGraph workflow asynchronously
    final_state = await agent_workflow.ainvoke(initial_state)
    
    # 3. Extract the final response from the agent's memory
    final_ai_message = final_state["messages"][-1].content
    
    # 4. Return a structured JSON response to the client
    return {
        "status": "Success",
        "issue_id": request.issue_id,
        "resolution_summary": final_ai_message,
        "pr_draft_details": final_state.get("pr_draft", None)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)