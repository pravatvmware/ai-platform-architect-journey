import subprocess
import logging
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime
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
REPORTS_DIR = ROOT_DIR / "reports"

def generate_infrastructure(env_name: str):
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
    except Exception as e:
        logging.error(f"Failed to generate infrastructure: {e}")
        sys.exit(1)

def run_terraform_command(command: list[str], stream_output: bool = True) -> bool:
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
    logging.info(f"Setting up Terraform Workspace for: {env_name.upper()}")
    select_cmd = subprocess.run(
        ["terraform", "workspace", "select", env_name],
        cwd=TERRAFORM_DIR, capture_output=True, text=True
    )
    if select_cmd.returncode != 0:
        logging.info(f"Workspace '{env_name}' not found. Creating it...")
        if not run_terraform_command(["terraform", "workspace", "new", env_name]):
            sys.exit("Pipeline halted: Failed to create environment workspace.")

def run_security_scan() -> tuple[bool, str]:
    """Runs Checkov and returns the success boolean and the report text."""
    logging.info("Running Checkov security scan on tfplan.json...")
    checkov_exe = shutil.which("checkov")
    
    if not checkov_exe:
        err_msg = "Checkov executable not found in the current environment."
        logging.error(err_msg)
        return False, err_msg

    try:
        result = subprocess.run(
            [checkov_exe, "-f", "tfplan.json", "--soft-fail"],
            cwd=TERRAFORM_DIR, capture_output=True, text=True
        )
        
        report_text = result.stdout if result.stdout else result.stderr
        
        if result.stdout:
            print("\n--- Checkov Report ---")
            print(result.stdout)
            print("----------------------\n")
            
        if result.returncode != 0:
            logging.error("🚨 SECURITY SCAN FAILED 🚨")
            return False, report_text
            
        logging.info("✅ SECURITY SCAN COMPLETED.")
        return True, report_text
        
    except Exception as e:
        err_msg = f"Failed to execute Checkov: {e}"
        logging.error(err_msg)
        return False, err_msg

def publish_report(env_name: str, checkov_report: str):
    """Generates a consolidated Markdown artifact for the pipeline run."""
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Use terraform show to get the human-readable text of the plan
    plan_result = subprocess.run(
        ["terraform", "show", "-no-color", "tfplan"],
        cwd=TERRAFORM_DIR, capture_output=True, text=True
    )
    plan_text = plan_result.stdout

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = REPORTS_DIR / f"{env_name}_execution_report_{timestamp}.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Pipeline Execution Report: {env_name.upper()}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. Terraform Plan Summary\n")
        f.write("```terraform\n")
        f.write(plan_text.strip() if plan_text else "No changes required.")
        f.write("\n```\n\n")
        
        f.write("## 2. Checkov Security Scan\n")
        f.write("```text\n")
        f.write(checkov_report.strip() if checkov_report else "No security report generated.")
        f.write("\n```\n")

    logging.info(f"📄 Consolidated pipeline report published to: {report_file}")

def deploy(env_name: str):
    logging.info(f"Starting Pipeline for Environment: {env_name.upper()}")

    generate_infrastructure(env_name)

    if not run_terraform_command(["terraform", "init"]):
        sys.exit("Pipeline halted: Failed at terraform init.")

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

    # Run the scan and capture both the status and the report text
    scan_passed, checkov_text = run_security_scan()
    
    # Publish the report before applying (or exiting) so we have a record of failures
    publish_report(env_name, checkov_text)

    if not scan_passed:
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