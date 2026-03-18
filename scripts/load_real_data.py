#!/usr/bin/env python
"""
Load all real data into the system
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def load_real_data():
    """Load all real constraints into the system"""
    
    print("="*60)
    print("📥 LOADING REAL TIMETABLE DATA")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/status")
        print("✅ Server is running")
    except:
        print("❌ Server not running. Start with: python run.py server")
        return
    
    # 1. Reset system
    print("\n🔄 Resetting system...")
    response = requests.post(f"{BASE_URL}/reset")
    print(f"   {response.json()}")
    
    # 2. Create structure
    print("\n📅 Creating timetable structure...")
    structure_path = Path("data/structure.json")
    if not structure_path.exists():
        print("❌ structure.json not found!")
        return
    
    with open(structure_path) as f:
        structure = json.load(f)
    
    response = requests.post(f"{BASE_URL}/structure", json=structure)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Structure created with {result['slot_count']} slots")
        print(f"   Days: {', '.join(result['days'])}")
    else:
        print(f"❌ Failed: {response.text}")
        return
    
    # 3. Load real constraints
    print("\n📚 Loading real constraints...")
    constraints_path = Path("data/real/complete_constraints.json")
    if not constraints_path.exists():
        print("❌ complete_constraints.json not found!")
        print("   Run extract_real_constraints.py first")
        return
    
    with open(constraints_path) as f:
        constraints = json.load(f)
    
    print(f"   Loading {len(constraints)} constraints...")
    response = requests.post(f"{BASE_URL}/constraints/batch", json=constraints)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Added {result['added']} constraints")
        if result['failed'] > 0:
            print(f"   ⚠️ {result['failed']} constraints failed")
            if result['errors']:
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"      - {error}")
    else:
        print(f"❌ Failed: {response.text}")
        return
    
    # 4. Check final status
    print("\n📊 Final system status:")
    response = requests.get(f"{BASE_URL}/status")
    if response.status_code == 200:
        status = response.json()
        print(json.dumps(status, indent=2))
    
    # 5. Ask if user wants to solve
    print("\n" + "="*60)
    solve = input("🔄 Generate timetable now? (y/n): ")
    if solve.lower() == 'y':
        print("\n⚙️ Solving timetable...")
        response = requests.post(f"{BASE_URL}/solve")
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'feasible':
                print("✅ FEASIBLE SOLUTION FOUND!")
                assigned = sum(1 for v in result['assignments'].values() if v == 1)
                total = len(result['assignments'])
                print(f"   Assigned: {assigned}/{total} slots")
                
                # Save solution
                with open("data/real/timetable_solution.json", 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"💾 Solution saved to data/real/timetable_solution.json")
            else:
                print(f"❌ No feasible solution: {result['status']}")
        else:
            print(f"❌ Solver error: {response.text}")
    
    print("\n🎉 Done!")


if __name__ == "__main__":
    load_real_data()