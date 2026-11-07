import subprocess
import logging
import sys
from pathlib import Path

# Fulfills Phase 1 standard logging requirement
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Point to the directory containing main.tf
TERRAFORM_DIR = Path(__file__).parent / "infrastructure"

def run_terraform_command(command: list[str]) -> bool:
    """Executes a Terraform command via subprocess and handles the output."""
    cmd_str = " ".join(command)
    logging.info(f"Executing: {cmd_str}")
    
    try:
        result = subprocess.run(
            command,
            cwd=TERRAFORM_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(f"Success: {cmd_str}\n{result.stdout}")
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {cmd_str} (Exit code: {e.returncode})")
        logging.error(f"Error output:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error("Terraform executable not found. Is it installed and in your PATH?")
        return False

def deploy():
    """Orchestrates the infrastructure deployment pipeline."""
    if not TERRAFORM_DIR.exists():
        logging.error(f"Infrastructure directory not found at {TERRAFORM_DIR}")
        sys.exit(1)

    logging.info("Starting Phase 1 Infrastructure Deployment (Local Docker)")

    # 1. Initialize Terraform (Downloads the Docker provider)
    if not run_terraform_command(["terraform", "init"]):
        sys.exit("Pipeline halted: Failed at terraform init.")

    # 2. Plan the deployment
    if not run_terraform_command(["terraform", "plan", "-out=tfplan"]):
        sys.exit("Pipeline halted: Failed at terraform plan.")

    # Convert the binary plan to a readable JSON file
    try:
        with open(TERRAFORM_DIR / "tfplan.json", "w") as f:
            subprocess.run(
                ["terraform", "show", "-json", "tfplan"],
                cwd=TERRAFORM_DIR,
                stdout=f,
                check=True
            )
        logging.info("Readable JSON plan saved to infrastructure/tfplan.json")
    except subprocess.CalledProcessError:
        logging.error("Failed to convert tfplan to JSON.")

    # 3. Apply the infrastructure changes
    if not run_terraform_command(["terraform", "apply", "-auto-approve", "tfplan"]):
        sys.exit("Pipeline halted: Failed at terraform apply.")

    logging.info("Deployment successful! You can view the container in Docker Desktop.")
    logging.info("Test it by opening http://localhost:8080 in your browser.")

if __name__ == "__main__":
    deploy()