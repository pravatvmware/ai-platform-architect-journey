import docker
import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

ROOT_DIR = Path(__file__).parent
CONFIGS_DIR = ROOT_DIR / "configs"
REPORTS_DIR = ROOT_DIR / "reports"

def load_config(env_name: str) -> dict:
    """Loads the intended infrastructure state from the environment config."""
    config_file = CONFIGS_DIR / f"{env_name}.json"
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file.name} not found.")
        sys.exit(1)

def detect_drift(env_name: str):
    """Compares intended state (JSON) against live state (Docker API) and generates a report."""
    logging.info(f"Starting Drift Detection for Environment: {env_name.upper()}")
    
    expected_config = load_config(env_name)
    expected_containers = expected_config.get("containers", [])
    
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        logging.error("Could not connect to Docker. Is Docker Desktop running?")
        sys.exit(1)

    drift_detected = False
    audit_logs = []
    
    msg = f"Auditing {len(expected_containers)} expected resources..."
    logging.info(msg)
    audit_logs.append(msg)

    for expected in expected_containers:
        container_name = expected["name"]
        expected_ext_port = expected["external_port"]
        
        try:
            live_container = client.containers.get(container_name)
            
            # 1. Verify Status
            if live_container.status != "running":
                msg = f"❌ DRIFT: Container '{container_name}' exists but is {live_container.status} (Expected: running)."
                logging.warning(msg)
                audit_logs.append(msg)
                drift_detected = True
                continue
            
            # 2. Verify Port Bindings
            ports = live_container.attrs['NetworkSettings']['Ports']
            tcp_80 = ports.get('80/tcp')
            
            if tcp_80:
                live_ext_port = int(tcp_80[0]['HostPort'])
                if live_ext_port != expected_ext_port:
                    msg = f"❌ DRIFT: Container '{container_name}' port mismatch. Live: {live_ext_port}, Expected: {expected_ext_port}"
                    logging.warning(msg)
                    audit_logs.append(msg)
                    drift_detected = True
                else:
                    msg = f"✅ Verified: '{container_name}' is running securely on port {live_ext_port}."
                    logging.info(msg)
                    audit_logs.append(msg)
            else:
                msg = f"❌ DRIFT: Container '{container_name}' is not exposing port 80 as expected."
                logging.warning(msg)
                audit_logs.append(msg)
                drift_detected = True

        except docker.errors.NotFound:
            msg = f"🚨 MAJOR DRIFT: Expected container '{container_name}' is missing entirely from the infrastructure!"
            logging.error(msg)
            audit_logs.append(msg)
            drift_detected = True

    # Generate the Markdown Artifact
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = REPORTS_DIR / f"{env_name}_drift_report_{timestamp}.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Drift Detection Report: {env_name.upper()}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Audit Log\n```text\n")
        f.write("\n".join(audit_logs))
        f.write("\n```\n\n")
        
        f.write("## Summary\n")
        if drift_detected:
            f.write("**Status:** 🚨 INFRASTRUCTURE DRIFT DETECTED 🚨\n\n")
            f.write("Manual intervention or Terraform apply required to bring infrastructure back to expected state.")
        else:
            f.write("**Status:** ✅ PERFECT MATCH\n\n")
            f.write("Infrastructure perfectly matches the configuration. No drift detected.")

    print("\n--- Drift Detection Summary ---")
    if drift_detected:
        logging.error(f"Infrastructure drift detected. Report saved to: {report_file}")
        sys.exit(1)
    else:
        logging.info(f"Infrastructure perfectly matches configuration. Report saved to: {report_file}")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Infrastructure Drift Detector")
    parser.add_argument("--env", type=str, required=True, choices=["dev", "uat", "prod"], help="Target environment to audit")
    args = parser.parse_args()
    
    detect_drift(args.env)