from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent.graph import app as agent_workflow

app = FastAPI(title="Enterprise AI Agent API")

# 1. Define the Expected Request Body for Swagger UI
class IssueRequest(BaseModel):
    issue_id: int
    description: str

# 2. Update the endpoint to accept the request body
@app.post("/agent/issues/resolve")
async def resolve_issue(request: IssueRequest):
    # Pass the dynamic data from Swagger into the LangGraph state
    initial_state = {
        "issue_id": request.issue_id,
        "messages": [HumanMessage(content=f"Please resolve this issue: {request.description}")]
    }
    
    # Run the graph
    final_state = await agent_workflow.ainvoke(initial_state)
    
    return {
        "status": "success",
        "issue_id": request.issue_id,
        "agent_response": final_state["messages"][-1].content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)