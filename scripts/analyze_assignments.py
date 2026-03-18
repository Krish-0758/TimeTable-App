# scripts/analyze_assignments.py
import json
from collections import defaultdict

with open('timetable_solution.json') as f:
    solution = json.load(f)

assignments = solution['assignments']

# Group by day
days = defaultdict(list)
for slot, val in assignments.items():
    if val == 1:
        day = slot.split('_')[0]
        days[day].append(slot)

print("📅 Assigned Slots by Day:")
for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
    count = len(days[day])
    print(f"  {day}: {count} slots")
    for slot in sorted(days[day])[:3]:  # Show first 3
        print(f"    - {slot}")