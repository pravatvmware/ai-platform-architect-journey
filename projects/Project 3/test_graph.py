from langchain_core.messages import HumanMessage
from agent.graph import app

def run_test():
    print("🚀 Starting Multi-Agent Supervisor Test...\n")
    
    # 1. The initial request (simulating a GitHub Issue)
    user_input = (
        "We have a security vulnerability in our Terraform codebase. "
        "Please read the code, draft a fix, and then deploy it as a Pull Request."
    )
    
    # 2. Package it into our State schema
    inputs = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    # 3. Stream the graph execution to watch the agents converse
    print(f"User: {user_input}")
    
    # We use stream() instead of invoke() so we can watch the routing happen step-by-step
    for output in app.stream(inputs, {"recursion_limit": 10}):
        for node_name, state_update in output.items():
            print(f"\n--- 🔄 Finished Execution: {node_name} ---")
            
            # If a worker agent generated a message, print it
            if "messages" in state_update and state_update["messages"]:
                latest_msg = state_update["messages"][-1].content
                print(f"Output:\n{latest_msg}")

    print("\n✅ Multi-Agent Workflow Complete!")

if __name__ == "__main__":
    run_test()