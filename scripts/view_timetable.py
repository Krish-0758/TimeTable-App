#!/usr/bin/env python
"""
View the generated timetable in a readable format
"""

import json
from collections import defaultdict

def view_timetable(solution_file="data/real/timetable_solution.json"):
    """Display the timetable in a readable format"""
    
    try:
        with open(solution_file) as f:
            solution = json.load(f)
    except FileNotFoundError:
        print(f"❌ Solution file not found: {solution_file}")
        return
    
    if solution['status'] != 'feasible':
        print(f"❌ No feasible solution: {solution['status']}")
        return
    
    assignments = solution['assignments']
    
    # Group by day
    days = defaultdict(list)
    for slot_id, value in assignments.items():
        if value == 1:  # Only show assigned slots
            # Parse slot_id: DAY_START_END_TYPE
            parts = slot_id.split('_')
            if len(parts) >= 4:
                day = parts[0]
                start = parts[1]
                end = parts[2]
                time_str = f"{start[:2]}:{start[2:]}-{end[:2]}:{end[2:]}"
                days[day].append((time_str, slot_id))
    
    # Sort by time
    day_order = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    day_names = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                 'THU': 'Thursday', 'FRI': 'Friday'}
    
    print("\n" + "="*80)
    print("📅 GENERATED TIMETABLE")
    print("="*80)
    
    total_assigned = 0
    for day_code in day_order:
        if day_code in days:
            slots = sorted(days[day_code], key=lambda x: x[0])
            print(f"\n{day_names[day_code]} ({len(slots)} lectures)")
            print("-" * 40)
            for time_str, slot_id in slots:
                print(f"  {time_str} : {slot_id}")
                total_assigned += 1
    
    print("\n" + "="*80)
    print(f"Total assigned lectures: {total_assigned}")
    print("="*80)


if __name__ == "__main__":
    view_timetable()