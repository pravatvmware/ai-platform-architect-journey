import subprocess
import logging
import sys
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

ROOT_DIR = Path(__file__).parent
TERRAFORM_DIR = ROOT_DIR / "infrastructure"
TEMPLATES_DIR = ROOT_DIR / "templates"

def generate_infrastructure():
    """Reads JSON config and generates Terraform code via Jinja2."""
    logging.info("Reading config.json...")
    try:
        with open(ROOT_DIR / "config.json", "r") as f:
            config = json.load(f)
            
        logging.info("Generating main.tf from template...")
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template("main.tf.j2")
        
        rendered_tf = template.render(config)
        
        TERRAFORM_DIR.mkdir(exist_ok=True)
        with open(TERRAFORM_DIR / "main.tf", "w") as f:
            f.write(rendered_tf)
            
        logging.info("Successfully generated infrastructure/main.tf")
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
            logging.info(f"Success: {cmd_str}")
        else:
            result = subprocess.run(
                command, cwd=TERRAFORM_DIR, check=True, capture_output=True, text=True
            )
            logging.info(f"Success: {cmd_str}\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {cmd_str} (Exit code: {e.returncode})")
        return False

def run_security_scan() -> bool:
    """Runs Checkov policy-as-code scanner against the Terraform plan."""
    logging.info("Running Checkov security scan on tfplan.json...")
    try:
        # Checkov returns a non-zero exit code if violations are found
        result = subprocess.run(
            ["checkov", "-f", "tfplan.json"],
            cwd=TERRAFORM_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logging.error("🚨 SECURITY SCAN FAILED 🚨")
            logging.error("Policy violations detected in the Terraform plan:")
            # Print the Checkov output so you can see exactly what failed
            print(result.stdout)
            return False
            
        logging.info("✅ SECURITY SCAN PASSED. No policy violations found.")
        return True
        
    except FileNotFoundError:
        logging.error("Checkov executable not found. Did you run 'pip install checkov'?")
        return False

def deploy():
    """Orchestrates the infrastructure deployment pipeline."""
    logging.info("Starting Phase 3: Enterprise Architecture & Security")

    # 0. Generate the .tf files dynamically
    generate_infrastructure()

    # 1. Initialize
    if not run_terraform_command(["terraform", "init"]):
        sys.exit("Pipeline halted: Failed at terraform init.")

    # 2. Plan
    if not run_terraform_command(["terraform", "plan", "-out=tfplan"]):
        sys.exit("Pipeline halted: Failed at terraform plan.")

    # 3. Export Plan to JSON
    try:
        with open(TERRAFORM_DIR / "tfplan.json", "w") as f:
            subprocess.run(
                ["terraform", "show", "-json", "tfplan"],
                cwd=TERRAFORM_DIR, stdout=f, check=True
            )
    except subprocess.CalledProcessError:
        logging.error("Failed to convert tfplan to JSON.")
        sys.exit(1)

    # 4. Security Scan (The Enterprise Gate)
    if not run_security_scan():
        sys.exit("Pipeline halted: Security policy violations detected.")

    # 5. Apply (Only runs if the security scan passes)
    if not run_terraform_command(["terraform", "apply", "-auto-approve", "tfplan"]):
        sys.exit("Pipeline halted: Failed at terraform apply.")

    logging.info("Deployment successful! View containers in Docker Desktop.")

if __name__ == "__main__":
    deploy()