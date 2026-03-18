# scripts/check_specials.py
import json

with open('data/real/all_constraints_fixed.json') as f:
    data = json.load(f)

print(f"Total constraints: {len(data)}")
print("\nLast 2 constraints:")
for i, constraint in enumerate(data[-2:], start=1):
    print(f"\n{i}. ID: {constraint['constraint_id']}")
    print(f"   Type: {constraint['constraint_type']}")
    print(f"   Hardness: {constraint['hardness']}")
    print(f"   Parameters: {constraint['parameters']}")
    