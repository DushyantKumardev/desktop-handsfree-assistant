"""Environment verification smoke test for Desktop Handsfree Assistant backend."""

import os
import sys
from pathlib import Path

def verify_environment() -> None:
    print("=" * 60)
    print("  Desktop Handsfree Assistant - Backend Environment Check")
    print("=" * 60)

    # 1. Python version check
    python_ver = sys.version.split()[0]
    print(f"[+] Python Version: {python_ver}")
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        print(f"[!] Warning: Python 3.10+ recommended (current: {major}.{minor})")
    else:
        print(f"[OK] Python version meets requirement (>= 3.10)")

    # 2. Virtual environment check
    in_venv = (sys.prefix != sys.base_prefix)
    prefix_path = Path(sys.prefix).resolve()
    print(f"[+] Active Prefix: {prefix_path}")
    if in_venv:
        print("[OK] Running inside an isolated virtual environment")
    else:
        print("[!] ERROR: Not running in a virtual environment!")
        sys.exit(1)

    # 3. Import check for foundational baseline package
    try:
        import dotenv
        from importlib.metadata import version
        pkg_version = version("python-dotenv")
        print(f"[OK] python-dotenv imported successfully (v{pkg_version})")
    except Exception as e:
        print(f"[!] ERROR: Failed to import python-dotenv: {e}")
        sys.exit(1)

    print("=" * 60)
    print("[SUCCESS] Backend environment is verified and healthy.")
    print("=" * 60)

if __name__ == "__main__":
    verify_environment()
