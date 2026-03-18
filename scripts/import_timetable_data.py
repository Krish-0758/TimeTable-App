# scripts/import_timetable_data.py
#!/usr/bin/env python

"""
Import raw timetable data and generate constraints
Usage: python import_timetable_data.py --excel "path/to/excel.xlsx" --output "data/"
"""

import argparse
import json
from pathlib import Path
from data_extractor import TimetableDataExtractor, ConstraintGenerator
import requests

class TimetableImporter:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.extractor = TimetableDataExtractor()
        self.generator = None
        
    def import_from_files(self, excel_path=None, master_timetable=None, 
                         personal_timetables=None, output_dir="data/"):
        """Main import function"""
        
        print("="*60)
        print("📥 TIMETABLE DATA IMPORTER")
        print("="*60)
        
        # Step 1: Extract data from Excel
        if excel_path:
            print(f"\n📊 Step 1: Extracting from Excel...")
            extracted = self.extractor.extract_from_excel(excel_path)
            print(f"   Found {len(self.extractor.faculties)} faculties")
            print(f"   Found {len(self.extractor.courses)} courses")
            print(f"   Found {len(self.extractor.assignments)} assignments")
        
        # Step 2: Generate constraints
        print(f"\n⚙️ Step 2: Generating constraints...")
        self.generator = ConstraintGenerator(self.extractor)
        constraints = self.generator.generate_all_constraints(output_dir)
        
        # Step 3: Import to API
        print(f"\n🚀 Step 3: Importing to API...")
        self._import_to_api(constraints, output_dir)
        
        print("\n✅ IMPORT COMPLETE!")
        print(f"   Constraints saved to: {output_dir}/")
        print(f"   Total constraints: {len(constraints)}")
        print("\n   Next steps:")
        print("   1. Start your server: python run.py server")
        print("   2. Load constraints: python run.py client batch-add data/complete_constraints.json")
        print("   3. Generate timetable: python run.py client solve")
        
    def _import_to_api(self, constraints, output_dir):
        """Optional: Auto-import to running API"""
        try:
            # Check if API is running
            response = requests.get(f"{self.api_url}/status")
            if response.status_code == 200:
                print("   ✅ API is running")
                
                # Create structure first
                structure_path = Path(output_dir) / "structure.json"
                if structure_path.exists():
                    with open(structure_path) as f:
                        structure = json.load(f)
                    response = requests.post(f"{self.api_url}/structure", json=structure)
                    if response.status_code == 200:
                        print("   ✅ Structure created")
                
                # Import constraints
                response = requests.post(f"{self.api_url}/constraints/batch", json=constraints)
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Imported {result['added']} constraints to API")
                    
        except requests.exceptions.ConnectionError:
            print("   ⚠️ API not running. Constraints saved locally only.")
            print("   Start server with: python run.py server")


def main():
    parser = argparse.ArgumentParser(description="Import timetable data and generate constraints")
    parser.add_argument("--excel", help="Path to subject allotment Excel file")
    parser.add_argument("--master", help="Path to master timetable Word doc")
    parser.add_argument("--personal", help="Path to personal timetables Word doc")
    parser.add_argument("--output", default="data/", help="Output directory for JSON files")
    parser.add_argument("--api", default="http://localhost:8000", help="API URL")
    parser.add_argument("--auto-import", action="store_true", help="Auto-import to API")
    
    args = parser.parse_args()
    
    if not args.excel and not args.master and not args.personal:
        print("❌ Please provide at least one input file")
        parser.print_help()
        return
    
    importer = TimetableImporter(api_url=args.api)
    importer.import_from_files(
        excel_path=args.excel,
        master_timetable=args.master,
        personal_timetables=args.personal,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()