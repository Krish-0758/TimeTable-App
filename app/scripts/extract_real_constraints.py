#!/usr/bin/env python
"""
Extract REAL constraints from AY 2025_2026 ODD SUBJECT ALLOTMENT_JULY 2025.xlsx
Generates complete constraint files for all faculties, courses, and rooms
"""

import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

class RealTimetableExtractor:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.faculties: Dict[str, Dict] = {}
        self.courses: Dict[str, Dict] = {}
        self.assignments: List[Dict] = []
        self.rooms: List[Dict] = self._get_standard_rooms()
        self.faculty_workload: Dict[str, int] = {}  # From personal timetables
        
    def _get_standard_rooms(self) -> List[Dict]:
        """Return the actual rooms from your master timetable"""
        return [
            # Lecture halls
            {"id": "LHC301", "name": "Lecture Hall Complex 301", "capacity": 60, "type": "lecture", "building": "LHC"},
            {"id": "LHC303", "name": "Lecture Hall Complex 303", "capacity": 60, "type": "lecture", "building": "LHC"},
            {"id": "LHC304", "name": "Lecture Hall Complex 304", "capacity": 60, "type": "lecture", "building": "LHC"},
            {"id": "LHC305", "name": "Lecture Hall Complex 305", "capacity": 60, "type": "lecture", "building": "LHC"},
            {"id": "LHC206", "name": "Lecture Hall Complex 206", "capacity": 50, "type": "lecture", "building": "LHC"},
            {"id": "LHC207", "name": "Lecture Hall Complex 207", "capacity": 50, "type": "lecture", "building": "LHC"},
            {"id": "LHC208", "name": "Lecture Hall Complex 208", "capacity": 50, "type": "lecture", "building": "LHC"},
            {"id": "LHC211", "name": "Lecture Hall Complex 211", "capacity": 50, "type": "lecture", "building": "LHC"},
            {"id": "ESB125", "name": "Engineering Sciences Block 125", "capacity": 40, "type": "lecture", "building": "ESB"},
            {"id": "ESB223", "name": "Engineering Sciences Block 223", "capacity": 40, "type": "lecture", "building": "ESB"},
            
            # Labs
            {"id": "CSE_LAB1", "name": "CSE Lab 1", "capacity": 30, "type": "lab", "building": "CSE Block"},
            {"id": "CSE_LAB2", "name": "CSE Lab 2", "capacity": 30, "type": "lab", "building": "CSE Block"},
            {"id": "CSE_LAB3", "name": "CSE Lab 3", "capacity": 30, "type": "lab", "building": "CSE Block"},
            {"id": "CSE_LAB4", "name": "CSE Lab 4", "capacity": 30, "type": "lab", "building": "CSE Block"},
            {"id": "PG_LAB1", "name": "PG Lab 1", "capacity": 20, "type": "lab", "building": "PG Block"},
            {"id": "PG_LAB2", "name": "PG Lab 2", "capacity": 20, "type": "lab", "building": "PG Block"},
        ]
    
    def _extract_section_from_course(self, course_str: str) -> str:
        """Extract section from course string like 'PPC(1)' or 'DBMS(5)'"""
        match = re.search(r'\((\d+)\)', course_str)
        if match:
            section_num = match.group(1)
            # Map section numbers to actual section names
            section_map = {
                '1': '1A',  # First year sections
                '2': '1B',
                '3': '3A',  # Third year sections
                '4': '3B',
                '5': '5A',  # Fifth year sections
                '6': '5B',
                '7': '7A',  # Seventh year sections
                '8': '7B',
                'K': '1K',  # Special sections
                'P': '1P',
                'T': '1T',
            }
            return section_map.get(section_num, f"SEC{section_num}")
        return "COMMON"
    
    def _generate_faculty_id(self, name: str) -> str:
        """Generate faculty ID from name (using initials from your documents)"""
        # Remove titles
        name = re.sub(r'^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+', '', name)
        name = name.strip()
        
        # Known faculty IDs from your documents
        known_ids = {
            'Dr. China Appala Naidu': 'RCA',
            'Dr. S.Seema': 'SS',
            'Dr. Monica R. Mundada': 'MRM',
            'Prof. Nagabhushan A M': 'NAM',
            'Dr.Shilpa S Chaudhari': 'SSC',
            'Dr.T.N R. Kumar': 'TNR',
            'Dr.Rajarajeswari S': 'SRR',
            'Dr.J.Sangeetha': 'SJ',
            'Dr.A Parkavi': 'APK',
            'Dr.J Geetha': 'JGR',
            'Dr.Dayananda R B': 'DRB',
            'Dr.Sangeetha V': 'SV',
            'Dr.Ganeshayya I Shidaganti': 'GIS',
            'Dr.Sushma B': 'SB',
            'Veena GS': 'VGS',
            'Dr.Mallegowda M': 'MG',
            'Dr.Chandrika Prasad': 'CP',
            'Pradeep kumar D': 'DPK',
            'Darshana A Naik': 'DN',
            'Jamuna S Murthy': 'JSM',
            'Nandini S B': 'NSB',
            'Soumya C S': 'SCS',
            'Akshata S Bhayyar': 'ASB',
            'Vishwachetan D': 'VCD',
            'Akshata Kamath': 'AKK',
            'Mamatha A': 'MA',
            'Pallavi N': 'PN',
            'Brunda': 'BG',
            'Uzma Sulthana': 'US',
            'Priya K': 'PK',
            'Dr. Manjula M C': 'MMC',
        }
        
        # Check if we have a known ID
        for full_name, fid in known_ids.items():
            if full_name in name or name in full_name:
                return fid
        
        # Fallback: generate from initials
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:3].upper()
    
    def _get_max_hours(self, designation: str) -> int:
        """Get max weekly hours based on designation"""
        des = designation.lower()
        if 'professor' in des and 'associate' not in des and 'assistant' not in des:
            return 24  # Professor
        elif 'associate professor' in des:
            return 22  # Associate Professor
        elif 'assistant professor' in des:
            return 20  # Assistant Professor
        elif 'head' in des:
            return 16  # Head of Department (less teaching)
        elif 'lecturer' in des:
            return 18  # Lecturer
        else:
            return 20  # Default
    
    def _get_course_name(self, code: str) -> str:
        """Get full course name from code"""
        course_names = {
            'PPC': 'Principles of Programming using C',
            'DMS': 'Discrete Mathematical Structures',
            'DBMS': 'Database Management Systems',
            'OS': 'Operating Systems',
            'DS': 'Data Structures',
            'OOP': 'Object Oriented Programming',
            'SE': 'Software Engineering',
            'AIML': 'AI and Machine Learning',
            'CNS': 'Cryptography and Network Security',
            'CD': 'Compiler Design',
            'MAP': 'Multicore Architecture and Programming',
            'SAN': 'Storage Area Networks',
            'SP': 'Secure Programming',
            'RM&IPR': 'Research Methodology & IPR',
            'UHV': 'Universal Human Values',
            'AEC': 'Ability Enhancement Course',
            'FSD': 'Full Stack Development',
            'DT': 'Design Thinking',
            'PLC': 'Programming Language Course',
            'IOT': 'Internet of Things',
            'VR': 'Virtual Reality',
            'ACN': 'Advanced Computer Networks',
            'ADBMS': 'Advanced Database Management Systems',
            'BIG DATA': 'Big Data Analytics',
            'MICROSERVICE': 'Microservices',
            'SKILL': 'Skill Enhancement Lab',
            'MATHS': 'Mathematics',
            'DD&CO': 'Digital Design and Computer Organization',
        }
        
        # Try exact match
        if code in course_names:
            return course_names[code]
        
        # Try partial match
        for key, name in course_names.items():
            if key in code:
                return name
        
        return code
    
    def extract_from_excel(self) -> None:
        """Extract all data from the Excel file"""
        print(f"📊 Reading Excel: {self.excel_path}")
        
        # Read all sheets
        excel_file = pd.ExcelFile(self.excel_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            print(f"  Processing sheet: {sheet_name}")
            
            # Look for the subject allotment section
            self._process_subject_allotment(df)
    
    def _process_subject_allotment(self, df: pd.DataFrame) -> None:
        """Process the subject allotment section"""
        
        # Find the header row (look for 'SI. No.', 'Name of Faculty', etc.)
        header_row = None
        for idx, row in df.iterrows():
            row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
            if 'SI. No.' in row_str and 'Name of Faculty' in row_str and 'Designation' in row_str:
                header_row = idx
                break
        
        if header_row is None:
            # Try alternate header format
            for idx, row in df.iterrows():
                row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
                if 'SI. No.' in row_str and 'Name of Faculty' in row_str:
                    header_row = idx
                    break
        
        if header_row is None:
            return
        
        # Get the headers
        headers = df.iloc[header_row].values
        data_rows = df.iloc[header_row + 1:].copy()
        
        # Process each faculty
        for idx, row in data_rows.iterrows():
            # Check if this is a faculty row
            if pd.isna(row.iloc[0]) or 'SI. No.' in str(row.iloc[0]):
                continue
            
            # Extract faculty info
            try:
                sl_no = row.iloc[0]
                if pd.isna(sl_no):
                    continue
                
                faculty_name = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else None
                if not faculty_name or faculty_name == 'nan':
                    continue
                
                designation = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 'Assistant Professor'
                
                # Generate faculty ID
                faculty_id = self._generate_faculty_id(faculty_name)
                
                # Store faculty
                if faculty_id not in self.faculties:
                    self.faculties[faculty_id] = {
                        'id': faculty_id,
                        'name': faculty_name,
                        'designation': designation,
                        'max_hours': self._get_max_hours(designation),
                        'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                        'max_consecutive': 2,
                        'min_break': 60,
                        'subjects': []
                    }
                    print(f"    Found faculty: {faculty_id} - {faculty_name}")
                
                # Extract subjects (columns after designation)
                # Look for Subject 1, Subject 2, Subject 3, LAB1, LAB 2
                for col_idx in range(3, min(len(row), 8)):  # Check up to 8 columns
                    subject_val = row.iloc[col_idx]
                    if pd.notna(subject_val) and subject_val != 'nan':
                        self._process_subject(str(subject_val), faculty_id)
                        
            except Exception as e:
                print(f"    Error processing row {idx}: {e}")
                continue
    
    def _process_subject(self, subject_str: str, faculty_id: str) -> None:
        """Process a subject string like 'PPC(1)' or 'DBMS(5) LAB'"""
        subject_str = subject_str.strip()
        
        # Parse course code and section
        # Pattern: CODE(SECTION) or CODE SECTION or CODE LAB
        match = re.search(r'([A-Z&]+)[\s\(]*(\d+)?', subject_str)
        if match:
            course_code = match.group(1).strip()
            section_num = match.group(2) if match.group(2) else '1'
            
            # Clean up course code
            course_code = course_code.replace('&', '').replace(' ', '')
            
            # Get section name
            section_name = self._extract_section_from_course(subject_str)
            
            # Determine if it's a lab
            is_lab = 'LAB' in subject_str.upper()
            
            # Determine weekly lectures
            if is_lab:
                weekly_lectures = 1
                requires_lab = True
            else:
                weekly_lectures = 3  # Most theory courses have 3 lectures/week
                requires_lab = False
            
            # Create course ID with section
            course_id = f"{course_code}_{section_name}"
            
            # Store course if new
            if course_id not in self.courses:
                self.courses[course_id] = {
                    'id': course_id,
                    'code': course_code,
                    'name': self._get_course_name(course_code),
                    'section': section_num,
                    'section_name': section_name,
                    'type': 'lab' if is_lab else 'theory',
                    'weekly_lectures': weekly_lectures,
                    'max_per_day': 1,
                    'requires_lab': requires_lab,
                    'faculty_ids': []
                }
                print(f"      New course: {course_id} ({section_name})")
            
            # Add faculty to course
            if faculty_id not in self.courses[course_id]['faculty_ids']:
                self.courses[course_id]['faculty_ids'].append(faculty_id)
            
            # Add course to faculty
            if course_id not in self.faculties[faculty_id]['subjects']:
                self.faculties[faculty_id]['subjects'].append(course_id)
            
            # Store assignment
            self.assignments.append({
                'faculty_id': faculty_id,
                'course_id': course_id,
                'type': 'lab' if is_lab else 'theory'
            })
            
            print(f"      Assigned: {course_id} to {faculty_id} ({'LAB' if is_lab else 'Theory'})")
    
    def generate_faculty_constraints(self) -> List[Dict]:
        """Generate faculty constraints from extracted data"""
        constraints = []
        
        for faculty_id, faculty in self.faculties.items():
            constraint = {
                "constraint_id": f"FAC_{faculty_id}",
                "constraint_type": "faculty",
                "hardness": "hard",
                "parameters": {
                    "faculty_id": faculty_id,
                    "faculty_name": faculty['name'],
                    "designation": faculty['designation'],
                    "max_hours_per_week": faculty['max_hours'],
                    "available_days": faculty['available_days'],
                    "max_consecutive_classes": faculty['max_consecutive'],
                    "min_break_minutes": faculty['min_break'],
                    "subjects": faculty['subjects']
                }
            }
            constraints.append(constraint)
        
        print(f"  Generated {len(constraints)} faculty constraints")
        return constraints
    
    # In extract_real_constraints.py, update the course generation:

def generate_course_constraints(self) -> List[Dict]:
    """Generate course/subject constraints with section tracking"""
    constraints = []
    
    for course_id, course in self.courses.items():
        constraint = {
            "constraint_id": f"SUB_{course_id}",
            "constraint_type": "subject",
            "hardness": "hard",
            "parameters": {
                "course_id": course_id,
                "course_code": course['code'],
                "course_name": course['name'],
                "section": course.get('section_name', 'COMMON'),
                "section_num": course.get('section', '1'),
                "type": course['type'],
                "weekly_lectures": course['weekly_lectures'],
                "max_lectures_per_day": course['max_per_day'],
                "requires_lab": course['requires_lab'],
                "faculty_ids": course['faculty_ids']  # List of faculty who can teach this
            }
        }
        constraints.append(constraint)
    
    return constraints
    
    def generate_special_constraints(self) -> List[Dict]:
        """Generate special constraints (Industry Talk, Proctor Meeting, etc.)"""
        constraints = [
            {
                "constraint_id": "SPECIAL_INDUSTRY_TALK_MON",
                "constraint_type": "special",
                "hardness": "hard",
                "parameters": {
                    "type": "industry_talk",
                    "day": "Monday",
                    "start_time": "15:35",
                    "end_time": "16:30",
                    "description": "Industry Talk / Training"
                }
            },
            {
                "constraint_id": "SPECIAL_PROCTOR_FRI",
                "constraint_type": "special",
                "hardness": "hard",
                "parameters": {
                    "type": "proctor_meeting",
                    "day": "Friday",
                    "start_time": "13:45",
                    "end_time": "14:40",
                    "description": "Proctor Meeting / College Activities"
                }
            }
        ]
        
        print(f"  Generated {len(constraints)} special constraints")
        return constraints
    
    def save_all(self, output_dir: str = "data/real/"):
        """Save all generated constraints to files"""
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate all constraints
        faculty_constraints = self.generate_faculty_constraints()
        course_constraints = self.generate_course_constraints()
        room_constraints = self.generate_room_constraints()
        special_constraints = self.generate_special_constraints()
        
        # Save individual files
        with open(f"{output_dir}/faculty_constraints.json", 'w') as f:
            json.dump(faculty_constraints, f, indent=2)
        
        with open(f"{output_dir}/course_constraints.json", 'w') as f:
            json.dump(course_constraints, f, indent=2)
        
        with open(f"{output_dir}/room_constraints.json", 'w') as f:
            json.dump(room_constraints, f, indent=2)
        
        with open(f"{output_dir}/special_constraints.json", 'w') as f:
            json.dump(special_constraints, f, indent=2)
        
        # Save complete file with all constraints
        all_constraints = faculty_constraints + course_constraints + room_constraints + special_constraints
        with open(f"{output_dir}/complete_constraints.json", 'w') as f:
            json.dump(all_constraints, f, indent=2)
        
        # Save summary
        summary = {
            "faculties": len(self.faculties),
            "courses": len(self.courses),
            "assignments": len(self.assignments),
            "rooms": len(self.rooms),
            "total_constraints": len(all_constraints)
        }
        
        with open(f"{output_dir}/summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 EXTRACTION SUMMARY")
        print("="*60)
        print(f"Faculties found: {len(self.faculties)}")
        print(f"Courses found: {len(self.courses)}")
        print(f"Assignments found: {len(self.assignments)}")
        print(f"Rooms configured: {len(self.rooms)}")
        print(f"\nConstraints generated:")
        print(f"  - Faculty constraints: {len(faculty_constraints)}")
        print(f"  - Course constraints: {len(course_constraints)}")
        print(f"  - Room constraints: {len(room_constraints)}")
        print(f"  - Special constraints: {len(special_constraints)}")
        print(f"  - TOTAL: {len(all_constraints)}")
        print("="*60)
        print(f"\n✅ Files saved to: {output_dir}")
        print("   - faculty_constraints.json")
        print("   - course_constraints.json")
        print("   - room_constraints.json")
        print("   - special_constraints.json")
        print("   - complete_constraints.json")
        print("   - summary.json")
        
        return all_constraints


def main():
    # Path to your Excel file
    excel_path = "AY 2025_2026 ODD SUBJECT ALLOTMENT_JULY 2025.xlsx"
    
    # Check if file exists
    if not Path(excel_path).exists():
        print(f"❌ Excel file not found: {excel_path}")
        print("Please make sure the file is in the current directory")
        return
    
    # Extract and save
    extractor = RealTimetableExtractor(excel_path)
    extractor.extract_from_excel()
    extractor.save_all()
    
    print("\n🎉 REAL DATA EXTRACTION COMPLETE!")
    print("\nNext steps:")
    print("1. Start your server: python run.py server")
    print("2. Create structure: python run.py client create-structure data/structure.json")
    print("3. Load real constraints: python run.py client batch-add data/real/complete_constraints.json")
    print("4. Generate timetable: python run.py client solve")
    print("5. Check results: python run.py client status")


if __name__ == "__main__":
    main()