# scripts/data_extractor.py
"""
Extract faculty, courses, rooms, and constraints from raw documents
"""

import pandas as pd
import json
import re
from typing import List, Dict, Any
from pathlib import Path

class TimetableDataExtractor:
    def __init__(self):
        self.faculties = []
        self.courses = []
        self.rooms = []
        self.assignments = []
        self.constraints = []
        
    def extract_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """Extract data from subject allotment Excel"""
        print(f"📊 Reading Excel: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=None)
        
        # Extract faculty list (from first sheet)
        self._extract_faculties(df)
        
        # Extract course assignments
        self._extract_course_assignments(df)
        
        return {
            "faculties": self.faculties,
            "courses": self.courses,
            "assignments": self.assignments
        }
    
    def _extract_faculties(self, df):
        """Extract faculty from the Excel"""
        # Look for the faculty list section
        for sheet_name, sheet in df.items():
            # Find rows that look like faculty entries
            for idx, row in sheet.iterrows():
                # Pattern: SI. No., Name, Designation
                if pd.notna(row.get('SI. No.')) and pd.notna(row.get('Name of Faculty')):
                    faculty = {
                        "id": self._generate_faculty_id(row['Name of Faculty']),
                        "name": row['Name of Faculty'],
                        "designation": row.get('Designation', 'Assistant Professor'),
                        "max_hours": self._get_max_hours(row.get('Designation', '')),
                        "subjects": []
                    }
                    self.faculties.append(faculty)
    
    def _extract_course_assignments(self, df):
        """Extract which faculty teaches which course"""
        for sheet_name, sheet in df.items():
            if 'ODD SEMESTER' in str(sheet.columns):
                # This is the subject allotment sheet
                for idx, row in sheet.iterrows():
                    if pd.notna(row.get('Name of Faculty')):
                        faculty_name = row['Name of Faculty']
                        faculty_id = self._generate_faculty_id(faculty_name)
                        
                        # Check each subject column
                        for col in ['Subject 1', 'Subject 2', 'Subject 3', 'LAB1', 'LAB 2']:
                            if pd.notna(row.get(col)):
                                course_info = row[col]
                                # Parse course code and section
                                course = self._parse_course(course_info, faculty_id)
                                if course:
                                    self.courses.append(course)
                                    self.assignments.append({
                                        "faculty_id": faculty_id,
                                        "course_code": course["code"],
                                        "section": course.get("section", "A"),
                                        "type": "lab" if "LAB" in col else "theory"
                                    })
    
    def extract_from_master_timetable(self, docx_path: str) -> List[Dict]:
        """Extract existing schedule patterns as constraints"""
        # This would parse the master timetable to learn:
        # - Which rooms are used for which sections
        # - Lab allocations
        # - Break patterns
        print(f"📅 Reading Master Timetable: {docx_path}")
        # Implementation would use python-docx to parse
        pass
    
    def extract_from_personal_timetables(self, docx_path: str) -> List[Dict]:
        """Extract faculty workload and availability"""
        print(f"👨‍🏫 Reading Personal Timetables: {docx_path}")
        # Parse each faculty's schedule to get:
        # - Their teaching hours
        # - Free slots
        # - Preferred times
        pass
    
    def _generate_faculty_id(self, name: str) -> str:
        """Generate ID from name (e.g., Dr.Annapurna P. Patil -> AP)"""
        # Extract initials
        words = name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        return name[:2].upper()
    
    def _get_max_hours(self, designation: str) -> int:
        """Set max hours based on designation"""
        if 'Professor' in designation:
            return 24
        elif 'Associate' in designation:
            return 22
        else:
            return 20
    
    def _parse_course(self, course_str: str, faculty_id: str) -> Dict:
        """Parse course string like 'PPC(1)' or 'DBMS(5) LAB'"""
        # Extract course code and section
        match = re.match(r'([A-Z]+)\((\d+)\)', course_str)
        if match:
            code = match.group(1)
            section = match.group(2)
            return {
                "code": code,
                "name": self._get_course_name(code),
                "credits": 4 if "LAB" in course_str else 3,
                "section": section,
                "faculty_id": faculty_id
            }
        return None
    
    def _get_course_name(self, code: str) -> str:
        """Map course codes to full names"""
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
            'SAN': 'Storage Area Networks'
        }
        return course_names.get(code, code)


class ConstraintGenerator:
    """Generate constraint JSON files from extracted data"""
    
    def __init__(self, extractor: TimetableDataExtractor):
        self.extractor = extractor
        self.constraints = []
        
    def generate_faculty_constraints(self) -> List[Dict]:
        """Generate faculty constraints JSON"""
        constraints = []
        for faculty in self.extractor.faculties:
            constraint = {
                "constraint_id": f"FAC_{faculty['id']}",
                "constraint_type": "faculty",
                "hardness": "hard",
                "parameters": {
                    "faculty_id": faculty['id'],
                    "name": faculty['name'],
                    "designation": faculty['designation'],
                    "max_hours_per_week": faculty['max_hours'],
                    "subjects": list(set([a['course_code'] for a in self.extractor.assignments 
                                        if a['faculty_id'] == faculty['id']]))
                }
            }
            constraints.append(constraint)
        return constraints
    
    def generate_course_constraints(self) -> List[Dict]:
        """Generate course constraints JSON"""
        constraints = []
        courses_seen = set()
        
        for assignment in self.extractor.assignments:
            course_code = assignment['course_code']
            if course_code not in courses_seen:
                constraint = {
                    "constraint_id": f"SUB_{course_code}",
                    "constraint_type": "subject",
                    "hardness": "hard",
                    "parameters": {
                        "course_code": course_code,
                        "name": self.extractor._get_course_name(course_code),
                        "weekly_lectures": 3,  # Default, would be extracted
                        "max_lectures_per_day": 1,
                        "requires_lab": "LAB" in assignment['type'].upper()
                    }
                }
                constraints.append(constraint)
                courses_seen.add(course_code)
        return constraints
    
    def generate_room_constraints(self) -> List[Dict]:
        """Generate room constraints JSON"""
        # This would come from master timetable
        rooms = [
            {"id": "LHC301", "capacity": 60, "type": "lecture"},
            {"id": "LHC303", "capacity": 60, "type": "lecture"},
            {"id": "LHC304", "capacity": 60, "type": "lecture"},
            {"id": "LHC305", "capacity": 60, "type": "lecture"},
            {"id": "CSE_LAB1", "capacity": 30, "type": "lab"},
            {"id": "CSE_LAB2", "capacity": 30, "type": "lab"},
            {"id": "CSE_LAB3", "capacity": 30, "type": "lab"},
            {"id": "CSE_LAB4", "capacity": 30, "type": "lab"},
        ]
        
        constraints = []
        for room in rooms:
            constraint = {
                "constraint_id": f"RM_{room['id']}",
                "constraint_type": "room",
                "hardness": "hard",
                "parameters": room
            }
            constraints.append(constraint)
        return constraints
    
    def generate_all_constraints(self, output_dir: str = "data/"):
        """Generate all constraint JSON files"""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate faculty constraints
        faculty_constraints = self.generate_faculty_constraints()
        with open(f"{output_dir}/faculty_constraints.json", 'w') as f:
            json.dump(faculty_constraints, f, indent=2)
        print(f"✅ Generated {len(faculty_constraints)} faculty constraints")
        
        # Generate course constraints
        course_constraints = self.generate_course_constraints()
        with open(f"{output_dir}/course_constraints.json", 'w') as f:
            json.dump(course_constraints, f, indent=2)
        print(f"✅ Generated {len(course_constraints)} course constraints")
        
        # Generate room constraints
        room_constraints = self.generate_room_constraints()
        with open(f"{output_dir}/room_constraints.json", 'w') as f:
            json.dump(room_constraints, f, indent=2)
        print(f"✅ Generated {len(room_constraints)} room constraints")
        
        # Generate complete batch file
        all_constraints = faculty_constraints + course_constraints + room_constraints
        with open(f"{output_dir}/complete_constraints.json", 'w') as f:
            json.dump(all_constraints, f, indent=2)
        print(f"✅ Generated complete constraints file with {len(all_constraints)} constraints")
        
        return all_constraints