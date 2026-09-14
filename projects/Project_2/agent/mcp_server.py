import sys
from mcp.server.mcpserver import MCPServer

# Initialize the MCP Server (v2.x syntax)
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
    """Submits a pull request to resolve a GitHub issue."""
    print(f"[MCP Server] Executing submit_github_pr for Issue #{issue_id}", file=sys.stderr)
    return f"Successfully created PR for Issue #{issue_id}: {fix_description}"

if __name__ == "__main__":
    mcp.run(transport="stdio")