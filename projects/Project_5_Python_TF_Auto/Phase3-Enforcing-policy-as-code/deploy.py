import subprocess
import logging
import sys
import json
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

ROOT_DIR = Path(__file__).parent
TERRAFORM_DIR = ROOT_DIR / "infrastructure"
TEMPLATES_DIR = ROOT_DIR / "templates"
CONFIGS_DIR = ROOT_DIR / "configs"

def generate_infrastructure(env_name: str):
    """Generates Terraform code based on the specific environment config."""
    config_file = CONFIGS_DIR / f"{env_name}.json"
    logging.info(f"Reading environment config: {config_file.name}...")
    
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template("main.tf.j2")
        rendered_tf = template.render(config)
        
        TERRAFORM_DIR.mkdir(exist_ok=True)
        with open(TERRAFORM_DIR / "main.tf", "w") as f:
            f.write(rendered_tf)
            
        logging.info(f"Successfully generated main.tf for {env_name.upper()} environment.")
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to generate infrastructure: {e}")
        sys.exit(1)

def run_terraform_command(command: list[str], stream_output: bool = True) -> bool:
    """Executes a Terraform command via subprocess."""
    cmd_str = " ".join(command)
    logging.info(f"Executing: {cmd_str}")
    
    try:
        if stream_output:
            subprocess.run(command, cwd=TERRAFORM_DIR, check=True)
        else:
            subprocess.run(
                command, cwd=TERRAFORM_DIR, check=True, capture_output=True, text=True
            )
        logging.info(f"Success: {cmd_str}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {cmd_str} (Exit code: {e.returncode})")
        return False

def setup_workspace(env_name: str):
    """Switches to the correct Terraform workspace (mimicking remote state separation)."""
    logging.info(f"Setting up Terraform Workspace for: {env_name.upper()}")
    
    # Try to select the workspace. If it fails (doesn't exist), create it.
    select_cmd = subprocess.run(
        ["terraform", "workspace", "select", env_name],
        cwd=TERRAFORM_DIR, capture_output=True, text=True
    )
    
    if select_cmd.returncode != 0:
        logging.info(f"Workspace '{env_name}' not found. Creating it...")
        if not run_terraform_command(["terraform", "workspace", "new", env_name]):
            sys.exit("Pipeline halted: Failed to create environment workspace.")

def run_security_scan() -> bool:
    """Runs Checkov policy-as-code scanner against the Terraform plan."""
    logging.info("Running Checkov security scan on tfplan.json...")
    try:
        result = subprocess.run(
            ["checkov", "-f", "tfplan.json"],
            cwd=TERRAFORM_DIR, capture_output=True, text=True
        )
        if result.returncode != 0:
            logging.error("🚨 SECURITY SCAN FAILED 🚨\n" + result.stdout)
            return False
        logging.info("✅ SECURITY SCAN PASSED.")
        return True
    except FileNotFoundError:
        logging.error("Checkov executable not found.")
        return False

def deploy(env_name: str):
    """Orchestrates the environment-specific deployment pipeline."""
    logging.info(f"Starting Pipeline for Environment: {env_name.upper()}")

    generate_infrastructure(env_name)

    if not run_terraform_command(["terraform", "init"]):
        sys.exit("Pipeline halted: Failed at terraform init.")

    # Workspace Switch (The Core of Environment Isolation)
    setup_workspace(env_name)

    if not run_terraform_command(["terraform", "plan", "-out=tfplan"]):
        sys.exit("Pipeline halted: Failed at terraform plan.")

    try:
        with open(TERRAFORM_DIR / "tfplan.json", "w") as f:
            subprocess.run(
                ["terraform", "show", "-json", "tfplan"],
                cwd=TERRAFORM_DIR, stdout=f, check=True
            )
    except subprocess.CalledProcessError:
        sys.exit("Pipeline halted: Failed to convert tfplan to JSON.")

    if not run_security_scan():
        sys.exit("Pipeline halted: Security policy violations detected.")

    if not run_terraform_command(["terraform", "apply", "-auto-approve", "tfplan"]):
        sys.exit("Pipeline halted: Failed at terraform apply.")

    logging.info(f"{env_name.upper()} Deployment successful!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Terraform Orchestrator")
    parser.add_argument(
        "--env", 
        type=str, 
        required=True, 
        choices=["dev", "uat", "prod"], 
        help="Target environment (dev, uat, prod)"
    )
    args = parser.parse_args()
    
    deploy(args.env)