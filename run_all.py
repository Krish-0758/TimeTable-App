#!/usr/bin/env python3
"""
Timetable Generator - Main Orchestrator
Run this script to generate complete timetable
"""

import os
import sys
import subprocess
from pathlib import Path

def ensure_directories():
    """Create necessary directories if they don't exist"""
    Path('data').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    Path('scripts').mkdir(exist_ok=True)

def run_script(script_name, description):
    """Run a Python script and check for errors"""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    
    # Script is in the scripts folder
    script_path = Path('scripts') / script_name
    
    if not script_path.exists():
        print(f"ERROR: {script_path} not found!")
        print("Please ensure all script files are in the 'scripts' folder")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.stderr and 'warning' not in result.stderr.lower():
            print("Errors:")
            print(result.stderr)
            return False
        
        return True
        
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    """Main execution flow"""
    print("\n" + "="*60)
    print("DEPARTMENT TIMETABLE GENERATOR")
    print("Academic Year 2025-2026 (ODD Semester)")
    print("="*60)
    
    # Check if data files exist
    data_dir = Path('data')
    required_files = [
        'AY 2025_2026 ODD SUBJECT ALLOTMENT_JULY 2025.xlsx',
        'Section wise Subject Allotment.docx'
    ]
    
    missing_files = []
    for file in required_files:
        if not (data_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("\nERROR: Missing required data files:")
        for file in missing_files:
            print(f"  - data/{file}")
        print("\nPlease ensure all data files are in the 'data' directory")
        print("Current files in data directory:")
        if data_dir.exists():
            for f in data_dir.iterdir():
                print(f"  - {f.name}")
        return
    
    # Step 1: Extract data
    if not run_script('extract_data.py', 'Extracting data from Excel and Word files'):
        print("Failed to extract data")
        return
    
    # Step 2: Generate constraints
    if not run_script('generate_constraints.py', 'Generating constraints'):
        print("Failed to generate constraints")
        return
    
    # Step 3: Solve timetable
    if not run_script('solve_timetable.py', 'Solving timetable using CP-SAT'):
        print("Failed to generate timetable solution")
        return
    
    # Step 4: Generate HTML visualization
    if not run_script('visualize_timetable.py', 'Generating HTML visualization'):
        print("Failed to generate HTML timetable")
        return
    
    print("\n" + "="*60)
    print("✓ TIMETABLE GENERATION COMPLETE!")
    print("="*60)
    print("\nOutput files:")
    print("  - output/timetable.html (Open in browser to view)")
    print("  - output/timetable_solution.json (Raw solution data)")
    print("  - output/all_constraints.json (Constraints used)")
    print("\nYou can now open output/timetable.html in your browser")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ensure_directories()
    main()