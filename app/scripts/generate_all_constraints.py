# scripts/generate_all_constraints.py
from universal_parser import UniversalTimetableParser

parser = UniversalTimetableParser()

# This will create ALL the correct per-section constraints!
constraints = parser.generate_constraints(
    excel_file="AY 2025_2026 ODD SUBJECT ALLOTMENT_JULY 2025.xlsx",
    docx_file="Section wise Subject Allotment.docx"
)

print(f"✅ Generated {len(constraints)} per-section constraints")
# Should print: ✅ Generated 82 per-section constraints