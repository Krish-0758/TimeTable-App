# scripts/fix_special_constraints.py
import json

# Load the original file
with open('data/real/complete_constraints.json') as f:
    all_constraints = json.load(f)

# The last 2 items are special constraints
special = all_constraints[-2:]

# Fix their type
for s in special:
    s['constraint_type'] = 'special'
    print(f"Fixed: {s['constraint_id']}")

# Create a new file with all constraints
with open('data/real/all_constraints_fixed.json', 'w') as f:
    json.dump(all_constraints, f, indent=2)

print(f"\n✅ Created file with {len(all_constraints)} constraints (including specials)")