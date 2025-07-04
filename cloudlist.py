#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    """Entry point: Validate input, check dependencies and handle results."""
    if len(sys.argv) < 2:
        print("[!] Error: Please provide a cloud_provider for cloudlist run")
        print("Usage: python3 cloudlist.py example.com")
        sys.exit(1)
    
    cloud_provider = sys.argv[1]

    if not check_cloudlist_installed():
        print("[!] Error: cloudlist is not installed or not in PATH")
        print("Please install cloudlist first: https://cloudlist.projectdiscovery.io/cloudlist/get-started/")
        sys.exit(1)
    
    activate_venv()
    
    print(f"[*] Starting cloudlist run for: {cloud_provider}")
    exit_code = run_cloudlist_and_save(cloud_provider)
    
    if exit_code == 0:
        print("[+] cloudlist run completed successfully")
    else:
        print("[!] cloudlist run completed with errors or warnings. Provider config file required https://docs.projectdiscovery.io/tools/cloudlist/running") 
    
    sys.exit(exit_code)

def check_cloudlist_installed():
    """Return True if cloudlist is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["/go/bin/cloudlist", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def activate_venv():
    """Detect and note if a virtual environment exists."""
    venv_path = Path("venv")
    if venv_path.exists() and venv_path.is_dir():
        print("[*] Virtual environment found")
        venv_python = venv_path / "bin" / "python3"
        if venv_python.exists():
            print("[*] Using virtual environment Python")
        else:
            print("[*] Virtual environment found but Python not detected")

def run_cloudlist_and_save(cloud_provider):
    """Run cloudlist and save results to a timestamped file."""
    try:
        cloudlist_output = run_cloudlist(cloud_provider)
        if cloudlist_output is None:
            print("[!] cloudlist failed or returned no output")
            return 1
        
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        filename = f"{timestamp}-cloudlist.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(cloudlist_output)
        print(f"[*] cloudlist results saved as {filepath}")
        return 0

    except Exception as e:
        print(f"[!] Error running cloudlist: {e}", file=sys.stderr)
        return 1 

def run_cloudlist(provider):
    """Run cloudlist on the given cloud_provider and return its output as a string, or None on error."""
    command = [
        "/go/bin/cloudlist",
        "-provider", provider,
        "-silent"
    ]
    print(f"[*] Executing: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300,
            check=False
        )
        if result.returncode == -9:
            print("[!] Warning: cloudlist process was killed by SIGKILL (likely due to memory/resource limits)")
            if result.stdout.strip():
                return result.stdout
            return None
        if result.returncode != 0:
            print(f"[!] cloudlist exited with code {result.returncode}")
            if result.stderr:
                print("cloudlist error output:")
                print(result.stderr)
            return result.stdout if result.stdout.strip() else None
        return result.stdout
    except subprocess.TimeoutExpired:
        print("[!] cloudlist run timed out")
        return None
    except FileNotFoundError:
        print("[!] Error: cloudlist command not found. Please ensure cloudlist is installed and in PATH")
        return None
    except Exception as e:
        print(f"[!] Unexpected error running cloudlist: {e}")
        return None

if __name__ == "__main__":
    main() 