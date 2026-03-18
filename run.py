#!/usr/bin/env python3
"""
Convenience script to run the Timetable Generator server and client.

Usage:
    ./run.py server              # Start the API server
    ./run.py client status       # Check system status
    ./run.py client workflow examples/structure.json examples/faculty_constraint.json
    ./run.py test                 # Run tests (if pytest installed)
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Get the directory where this script is located
    base_dir = Path(__file__).parent.absolute()
    
    if command == "server":
        # Run the server
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload"] + args
        print(f"🚀 Starting server: {' '.join(cmd)}")
        print(f"📡 API will be available at http://localhost:8000")
        print(f"📚 API docs at http://localhost:8000/docs")
        print("\n" + "="*50 + "\n")
        subprocess.run(cmd, cwd=base_dir)
    
    elif command == "client":
        # Run the client
        cmd = [sys.executable, "-m", "scripts.client"] + args
        print(f"🖥️  Running client: {' '.join(cmd)}\n")
        subprocess.run(cmd, cwd=base_dir)
    
    elif command == "test":
        # Run tests (if pytest is installed)
        try:
            import pytest
            cmd = [sys.executable, "-m", "pytest", "tests/"] + args
            print(f"🧪 Running tests: {' '.join(cmd)}\n")
            subprocess.run(cmd, cwd=base_dir)
        except ImportError:
            print("❌ pytest not installed. Run: pip install pytest")
            sys.exit(1)
    
    elif command == "install":
        # Install dependencies
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        print(f"📦 Installing dependencies: {' '.join(cmd)}\n")
        subprocess.run(cmd, cwd=base_dir)
    
    elif command == "clean":
        # Clean Python cache files
        print("🧹 Cleaning Python cache files...")
        for path in base_dir.rglob("__pycache__"):
            print(f"   Removing {path}")
            import shutil
            shutil.rmtree(path)
        for path in base_dir.rglob("*.pyc"):
            print(f"   Removing {path}")
            path.unlink()
        print("✅ Clean complete")
    
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()