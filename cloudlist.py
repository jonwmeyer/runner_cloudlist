#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    """Entry point: Validate input, check dependencies, run wordlist generation, and handle results."""
    if len(sys.argv) < 2:
        print("[!] Error: Please provide a subdomain for wordlist generation")
        print("Usage: python3 naabu.py example.com")
        sys.exit(1)
    
    subdomain = sys.argv[1]

    if not check_naabu_installed():
        print("[!] Error: naabu is not installed or not in PATH")
        print("Please install naabu first: https://naabu.projectdiscovery.io/naabu/get-started/")
        sys.exit(1)
    
    activate_venv()
    
    print(f"[*] Starting naabu subdomain wordlist generation for: {subdomain}")
    exit_code = run_naabu_wordlist_generation_and_save(subdomain)
    
    if exit_code == 0:
        print("[+] wordlist generation completed successfully")
    else:
        print("[!] wordlist generation completed with errors or warnings")
    
    sys.exit(exit_code)

def check_naabu_installed():
    """Return True if naabu is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["/go/bin/naabu", "-version"],
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

def run_naabu_and_save(subdomain):
    """Run naabu and save results to a timestamped file."""
    try:
        naabu_output = run_naabu(subdomain)
        if naabu_output is None:
            print("[!] naabu failed or returned no output")
            return 1
        
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        filename = f"{timestamp}-naabu.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(naabu_output)
        print(f"[*] naabu results saved as {filepath}")
        return 0

    except Exception as e:
        print(f"[!] Error running naabu: {e}", file=sys.stderr)
        return 1 

def run_naabu(domain):
    """Run naabu on the given subdomain and return its output as a string, or None on error."""
    command = [
        "/go/bin/naabu",
        "-host", domain,
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
            print("[!] Warning: naabu process was killed by SIGKILL (likely due to memory/resource limits)")
            if result.stdout.strip():
                return result.stdout
            return None
        if result.returncode != 0:
            print(f"[!] naabu exited with code {result.returncode}")
            if result.stderr:
                print("naabu error output:")
                print(result.stderr)
            return result.stdout if result.stdout.strip() else None
        return result.stdout
    except subprocess.TimeoutExpired:
        print("[!] naabu wordlist generation timed out")
        return None
    except FileNotFoundError:
        print("[!] Error: naabu command not found. Please ensure naabu is installed and in PATH")
        return None
    except Exception as e:
        print(f"[!] Unexpected error running naabu: {e}")
        return None

if __name__ == "__main__":
    main() 