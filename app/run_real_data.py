#!/usr/bin/env python
"""
Master script to extract, load, and generate real timetable
"""

import subprocess
import sys
import time
import os

def main():
    print("="*60)
    print("🎓 REAL TIMETABLE GENERATION SYSTEM")
    print("="*60)
    
    # Step 1: Extract data from Excel
    print("\n📊 Step 1: Extracting real data from Excel...")
    result = subprocess.run([sys.executable, "scripts/extract_real_constraints.py"])
    if result.returncode != 0:
        print("❌ Extraction failed")
        return
    
    # Step 2: Ask if server is running
    print("\n" + "="*60)
    print("🚀 Step 2: Start the server")
    print("="*60)
    print("Open a NEW terminal and run: python run.py server")
    input("\nPress Enter AFTER the server is running...")
    
    # Step 3: Load data
    print("\n📥 Step 3: Loading real data...")
    result = subprocess.run([sys.executable, "scripts/load_real_data.py"])
    
    print("\n🎉 Complete! Check data/real/ for output files")

if __name__ == "__main__":
    main()