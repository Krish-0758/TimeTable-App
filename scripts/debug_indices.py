# scripts/debug_indices.py
import json

with open('data/real/all_constraints_fixed.json') as f:
    data = json.load(f)

print(f"Total constraints: {len(data)}")
print(f"\nConstraint at index 79:")
print(json.dumps(data[79], indent=2))
print(f"\nConstraint at index 80:")
print(json.dumps(data[80], indent=2))