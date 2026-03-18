# scripts/add_specials_to_structure.py
import json

# Load structure
with open('data/structure.json') as f:
    structure = json.load(f)

# Add industry talk as a break on Monday
structure['breaks'].append({
    "label": "Industry Talk",
    "start_time": "15:35",
    "end_time": "16:30"
})

# Add proctor meeting as a break on Friday
structure['breaks'].append({
    "label": "Proctor Meeting",
    "start_time": "13:45",
    "end_time": "14:40"
})

# Save updated structure
with open('data/structure_with_specials.json', 'w') as f:
    json.dump(structure, f, indent=2)

print("✅ Added special events as breaks in structure")
print(f"Total breaks: {len(structure['breaks'])}")