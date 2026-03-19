# scripts/universal_parser.py (COMPLETE VERSION)
"""
Universal parser that creates per-section constraints from Excel and Word files
"""

import re
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any

class UniversalTimetableParser:
    def __init__(self):
        self.patterns = {
            'course_code': r'([0-9]{2}[A-Z]{2}[0-9]{2,3})',
            'ratio': r'\((\d+):(\d+):(\d+)\)',
            'faculty_id': r'\(([A-Z]{2,4})\)',
            'semester': r'(\d+)[stndrd]{2} Semester',
        }
        self.faculty_map = {}  # Will store faculty name to ID mapping
        
    def parse_excel(self, filepath):
        """Parse Excel file - extracts faculty list and creates ID mapping"""
        print(f"📊 Reading Excel: {filepath}")
        df = pd.read_excel(filepath, sheet_name=0)
        
        # Find the faculty list section
        faculty_data = {}
        for idx, row in df.iterrows():
            if pd.notna(row.get('SI. No.')) and pd.notna(row.get('Name of Faculty')):
                name = str(row['Name of Faculty'])
                faculty_id = self._generate_faculty_id(name)
                faculty_data[faculty_id] = {
                    'name': name,
                    'designation': row.get('Designation', 'Professor')
                }
        
        return {'faculties': faculty_data}
    
    def _generate_faculty_id(self, name):
        """Generate faculty ID from name"""
        # Your existing ID generation logic from extract_real_constraints.py
        name = re.sub(r'^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+', '', name)
        known_ids = {
            'Dr. China Appala Naidu': 'RCA', 'Dr. S.Seema': 'SS',
            'Dr. Monica R. Mundada': 'MRM', 'Prof. Nagabhushan A M': 'NAM',
            'Dr.Shilpa S Chaudhari': 'SSC', 'Dr.T.N R. Kumar': 'TNR',
            'Dr.Rajarajeswari S': 'SRR', 'Dr.J.Sangeetha': 'SJ',
            'Dr.A Parkavi': 'APK', 'Dr.J Geetha': 'JGR',
            'Dr.Dayananda R B': 'DRB', 'Dr.Sangeetha V': 'SV',
            'Dr.Ganeshayya I Shidaganti': 'GIS', 'Dr.Sushma B': 'SB',
            'Veena GS': 'VGS', 'Dr.Mallegowda M': 'MG',
            'Dr.Chandrika Prasad': 'CP', 'Pradeep kumar D': 'DPK',
            'Darshana A Naik': 'DN', 'Jamuna S Murthy': 'JSM',
            'Nandini S B': 'NSB', 'Soumya C S': 'SCS',
            'Akshata S Bhayyar': 'ASB', 'Vishwachetan D': 'VCD',
            'Akshata Kamath': 'AKK', 'Mamatha A': 'MA',
            'Pallavi N': 'PN', 'Brunda': 'BG', 'Uzma Sulthana': 'US',
            'Priya K': 'PK', 'Dr. Manjula M C': 'MMC',
        }
        for full_name, fid in known_ids.items():
            if full_name in name or name in full_name:
                return fid
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:3].upper()
    
    def parse_docx(self, filepath):
        """Parse Word document - extracts section mappings and ratios"""
        from docx import Document
        
        doc = Document(filepath)
        tables = doc.tables
        
        section_mappings = {}
        weekly_hours = {}
        
        for table in tables:
            if len(table.rows) < 2:
                continue
                
            # Check if this is a semester table
            first_row = ' '.join([cell.text for cell in table.rows[0].cells])
            
            if 'Sl.No' in first_row and 'Course Code' in first_row:
                # This is a course allocation table
                self._parse_course_table(table, section_mappings, weekly_hours)
        
        return {
            'section_mappings': section_mappings,
            'weekly_hours': weekly_hours
        }
    
    def _parse_course_table(self, table, section_mappings, weekly_hours):
        """Parse a table showing faculty per section"""
        # Get headers
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        
        # Find section columns (A, B, C, D)
        section_cols = {}
        for i, header in enumerate(headers):
            if header in ['A', 'B', 'C', 'D']:
                section_cols[header] = i
        
        if not section_cols:
            return
        
        # Parse each data row
        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) < 2:
                continue
            
            # Extract course code
            course_match = re.search(self.patterns['course_code'], cells[0])
            if not course_match:
                continue
            course_code = course_match.group(1)
            
            # Extract ratio from course name
            ratio_match = re.search(self.patterns['ratio'], cells[1])
            if ratio_match:
                lecture, tutorial, lab = map(int, ratio_match.groups())
                weekly_hours[course_code] = {
                    'lecture': lecture,
                    'tutorial': tutorial,
                    'lab': lab
                }
            
            # Get semester from course code (e.g., 24CS32 -> 3)
            semester = course_code[2]
            
            # For each section, get faculty
            for section, col_idx in section_cols.items():
                if col_idx < len(cells):
                    faculty_cell = cells[col_idx]
                    faculty_match = re.search(self.patterns['faculty_id'], faculty_cell)
                    
                    if faculty_match:
                        faculty_id = faculty_match.group(1)
                        section_key = f"{semester}{section}"
                        
                        if section_key not in section_mappings:
                            section_mappings[section_key] = {}
                        
                        section_mappings[section_key][course_code] = {
                            'faculty': faculty_id
                        }
    
    def generate_constraints(self, excel_file, docx_file, output_file="data/real/per_section_constraints.json"):
        """Generate per-section constraints from both files"""
        
        # Parse both files
        excel_data = self.parse_excel(excel_file)
        docx_data = self.parse_docx(docx_file)
        
        constraints = []
        
        # For each section and course, create a constraint
        for section, courses in docx_data['section_mappings'].items():
            for course_code, details in courses.items():
                faculty_id = details['faculty']
                
                # Get hours from ratio (default 3:0:0 if not found)
                hours = docx_data['weekly_hours'].get(course_code, {'lecture': 3, 'tutorial': 0, 'lab': 0})
                
                # Create constraint
                constraint = {
                    "constraint_id": f"SUB_{course_code}_{section}",
                    "constraint_type": "subject",
                    "hardness": "hard",
                    "parameters": {
                        "course_id": f"{course_code}_{section}",
                        "course_code": course_code,
                        "course_name": f"Course {course_code}",
                        "section": section,
                        "weekly_lectures": hours['lecture'],
                        "weekly_tutorials": hours['tutorial'],
                        "weekly_labs": hours['lab'],
                        "requires_lab": hours['lab'] > 0,
                        "faculty_ids": [faculty_id]
                    }
                }
                constraints.append(constraint)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(constraints, f, indent=2)
        
        print(f"✅ Generated {len(constraints)} per-section constraints")
        return constraints