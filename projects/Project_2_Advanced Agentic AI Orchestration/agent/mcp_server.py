import sys
import os
from mcp.server.mcpserver import MCPServer
from github import Github

mcp = MCPServer("Enterprise-Infrastructure-Tools")

@mcp.tool()
def read_codebase(filepath: str) -> str:
    """Reads a file from the infrastructure codebase to analyze configurations."""
    print(f"[MCP Server] Executing read_codebase for: {filepath}", file=sys.stderr)
    
    if "vpc/main.tf" in filepath:
        return """
        resource "aws_vpc_security_group" "vpc-sc" {
          name = "vpc-sc"
          ingress {
            from_port   = 22
            protocol    = "tcp"
            cidr_blocks = ["0.0.0.0/0"]
          }
        }
        """
    return "Error: File not found."

@mcp.tool()
def submit_github_pr(issue_id: int, fix_description: str) -> str:
    """Submits a pull request (or comment) to resolve a GitHub issue."""
    print(f"[MCP Server] Executing submit_github_pr for Issue #{issue_id}", file=sys.stderr)
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable not set."
        
    try:
        # Authenticate with GitHub
        g = Github(token)
        
        # REPLACE THIS with your actual repository name!
        repo = g.get_repo("pravatvmware/ai-platform-architect-journey") 
        
        # Fetch the issue and post the AI's fix as a comment
        issue = repo.get_issue(number=issue_id)
        issue.create_comment(f"🤖 **Automated AI Fix Proposed:**\n\n{fix_description}")
        
        return f"Successfully posted AI fix to GitHub Issue #{issue_id}!"
    except Exception as e:
        return f"GitHub API Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")