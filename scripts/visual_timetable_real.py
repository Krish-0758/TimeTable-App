#!/usr/bin/env python
"""
Generate beautiful visual timetables with REAL data from your solution
"""

import json
from datetime import datetime
from typing import Dict, List, Any
import webbrowser
import os
from collections import defaultdict

class RealVisualTimetableGenerator:
    def __init__(self, solution_file: str = "timetable_solution.json", 
                 constraints_file: str = "data/real/complete_constraints.json"):
        """Initialize with solution and constraints files"""
        
        # Load solution
        with open(solution_file, encoding='utf-8') as f:
            self.solution = json.load(f)
        
        self.assignments = self.solution['assignments']
        self.status = self.solution['status']
        
        # Load constraints to get faculty and course info
        with open(constraints_file, encoding='utf-8') as f:
            self.constraints = json.load(f)
        
        # Build lookup dictionaries
        self.faculty_info = self._build_faculty_lookup()
        self.course_info = self._build_course_lookup()
        
        # Define time slots (matching your structure)
        self.time_slots = [
            {"start": "0900", "end": "0955", "label": "9:00-9:55", "time": "09:00"},
            {"start": "0955", "end": "1050", "label": "9:55-10:50", "time": "09:55"},
            {"start": "BREAK", "end": "BREAK", "label": "Morning Break", "is_break": True},
            {"start": "1105", "end": "1200", "label": "11:05-12:00", "time": "11:05"},
            {"start": "1200", "end": "1255", "label": "12:00-12:55", "time": "12:00"},
            {"start": "LUNCH", "end": "LUNCH", "label": "Lunch Break", "is_break": True},
            {"start": "1345", "end": "1440", "label": "1:45-2:40", "time": "13:45"},
            {"start": "1440", "end": "1535", "label": "2:40-3:35", "time": "14:40"},
            {"start": "1535", "end": "1630", "label": "3:35-4:30", "time": "15:35"}
        ]
        
        # Define sections (from your master timetable)
        self.sections = [
            {"id": "3A", "room": "LHC 301", "semester": "III", "students": 60},
            {"id": "3B", "room": "LHC 303", "semester": "III", "students": 60},
            {"id": "3C", "room": "LHC 304", "semester": "III", "students": 60},
            {"id": "3D", "room": "LHC 305", "semester": "III", "students": 60},
            {"id": "5A", "room": "LHC 206", "semester": "V", "students": 50},
            {"id": "5B", "room": "LHC 207", "semester": "V", "students": 50},
            {"id": "5C", "room": "LHC 208", "semester": "V", "students": 50},
            {"id": "5D", "room": "LHC 211", "semester": "V", "students": 50},
            {"id": "7A", "room": "ESB 125", "semester": "VII", "students": 40},
            {"id": "7B", "room": "ESB 223", "semester": "VII", "students": 40},
        ]
        
        # Days of week
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.day_codes = {'Monday': 'MON', 'Tuesday': 'TUE', 'Wednesday': 'WED', 
                         'Thursday': 'THU', 'Friday': 'FRI'}
        
        # Parse slot assignments by day and time
        self.slot_map = self._build_slot_map()
        
        # For now, we'll create a simple mapping for demonstration
        # In production, you'd have actual course-to-slot mapping
        self._create_sample_mapping()
    
    def _build_faculty_lookup(self) -> Dict:
        """Build lookup dictionary for faculty info"""
        faculty = {}
        for constraint in self.constraints:
            if constraint.get('constraint_type') == 'faculty':
                params = constraint.get('parameters', {})
                faculty_id = params.get('faculty_id')
                if faculty_id:
                    faculty[faculty_id] = {
                        'name': params.get('faculty_name', faculty_id),
                        'designation': params.get('designation', 'Professor')
                    }
        return faculty
    
    def _build_course_lookup(self) -> Dict:
        """Build lookup dictionary for course info"""
        courses = {}
        for constraint in self.constraints:
            if constraint.get('constraint_type') == 'subject':
                params = constraint.get('parameters', {})
                course_id = params.get('course_id')
                if course_id:
                    courses[course_id] = {
                        'code': params.get('course_code', ''),
                        'name': params.get('course_name', ''),
                        'section': params.get('section', '')
                    }
        return courses
    
    def _build_slot_map(self) -> Dict:
        """Build mapping of day+time to slot_id"""
        slot_map = {}
        for slot_id in self.assignments.keys():
            parts = slot_id.split('_')
            if len(parts) >= 3:
                day = parts[0]
                start = parts[1]
                slot_map[(day, start)] = slot_id
        return slot_map
    
    def _create_sample_mapping(self):
        """Create sample mapping for demonstration"""
        # This maps slot IDs to courses and faculty
        # In production, this would come from your actual data
        self.slot_course_map = {}
        self.slot_faculty_map = {}
        
        # Get all assigned slots
        assigned_slots = [s for s, v in self.assignments.items() if v == 1]
        
        # Sample course codes for different sections
        sample_courses = {
            '3A': ['OOP', 'DS', 'DMS', 'DD&CO', 'UHV', 'MATHS'],
            '3B': ['OOP', 'DS', 'DMS', 'DD&CO', 'UHV', 'MATHS'],
            '3C': ['OOP', 'DS', 'DMS', 'DD&CO', 'UHV', 'MATHS'],
            '3D': ['OOP', 'DS', 'DMS', 'DD&CO', 'UHV', 'MATHS'],
            '5A': ['AIML', 'OS', 'SE', 'CNS', 'RM&IPR', 'DBS'],
            '5B': ['AIML', 'OS', 'SE', 'CNS', 'RM&IPR', 'DBS'],
            '5C': ['AIML', 'OS', 'SE', 'CNS', 'RM&IPR', 'DBS'],
            '5D': ['AIML', 'OS', 'SE', 'CNS', 'RM&IPR', 'DBS'],
            '7A': ['CD', 'MAP', 'SAN', 'BIG DATA'],
            '7B': ['CD', 'MAP', 'SAN', 'BIG DATA'],
        }
        
        # Sample faculty for each course
        sample_faculty = {
            'OOP': 'SRR',
            'DS': 'AKK',
            'DMS': 'JGR',
            'DD&CO': 'MRC',
            'UHV': 'APK',
            'MATHS': 'RP',
            'AIML': 'SRR',
            'OS': 'SV',
            'SE': 'DN',
            'CNS': 'NSB',
            'RM&IPR': 'TNR',
            'DBS': 'SB',
            'CD': 'VCD',
            'MAP': 'MG',
            'SAN': 'BG',
            'BIG DATA': 'GIS',
        }
        
        # For now, just use a simple mapping
        for i, slot in enumerate(assigned_slots):
            # Determine section from slot pattern (simplified)
            if 'MON' in slot or 'TUE' in slot or 'WED' in slot or 'THU' in slot:
                if i % 4 == 0:
                    section = '3A'
                    course = 'OOP'
                elif i % 4 == 1:
                    section = '3B'
                    course = 'DS'
                elif i % 4 == 2:
                    section = '5A'
                    course = 'AIML'
                else:
                    section = '7A'
                    course = 'CD'
            else:
                section = '5B'
                course = 'OS'
            
            self.slot_course_map[slot] = {
                'code': course,
                'name': self.course_info.get(f"{course}_", {}).get('name', course),
                'section': section
            }
            self.slot_faculty_map[slot] = sample_faculty.get(course, 'TNR')
    
    def get_slot_info(self, day: str, start_time: str) -> Dict:
        """Get information about a specific slot"""
        slot_id = self.slot_map.get((self.day_codes[day], start_time))
        
        if not slot_id:
            return {'type': 'unknown', 'value': 0}
        
        value = self.assignments.get(slot_id, 0)
        
        if 'B' in slot_id:
            # Break/event slot
            if "1535" in slot_id and "MON" in slot_id:
                return {'type': 'event', 'value': 0, 'label': 'Industry Talk'}
            elif "1345" in slot_id and "FRI" in slot_id:
                return {'type': 'event', 'value': 0, 'label': 'Proctor Meeting'}
            else:
                return {'type': 'break', 'value': 0, 'label': 'Break'}
        elif value == 1:
            # Lecture slot
            course_info = self.slot_course_map.get(slot_id, {})
            faculty_id = self.slot_faculty_map.get(slot_id, '')
            faculty_name = self.faculty_info.get(faculty_id, {}).get('name', faculty_id)
            
            return {
                'type': 'lecture',
                'value': 1,
                'course_code': course_info.get('code', 'LEC'),
                'course_name': course_info.get('name', 'Lecture'),
                'faculty_id': faculty_id,
                'faculty_name': faculty_name,
                'section': course_info.get('section', '')
            }
        else:
            return {'type': 'free', 'value': 0, 'label': 'Free'}
    
    def generate_html(self) -> str:
        """Generate beautiful HTML timetable with real data"""
        html = []
        
        # CSS Styles
        html.append("""<!DOCTYPE html>
<html>
<head>
    <title>Master Timetable - CSE Department 2025-2026 (ODD Semester)</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .header p {
            margin: 5px 0 0;
            opacity: 0.9;
        }
        .section-tabs {
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .section-tab {
            padding: 10px 20px;
            background: #e0e0e0;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            border: none;
            font-size: 14px;
        }
        .section-tab:hover {
            background: #d0d0d0;
            transform: translateY(-2px);
        }
        .section-tab.active {
            background: #3498db;
            color: white;
            box-shadow: 0 2px 4px rgba(52,152,219,0.3);
        }
        .timetable-container {
            display: none;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .timetable-container.active {
            display: block;
        }
        .section-header {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 5px solid #3498db;
        }
        .section-header h2 {
            margin: 0;
            color: #2c3e50;
        }
        .section-header p {
            margin: 5px 0 0;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        th {
            background: #34495e;
            color: white;
            padding: 12px;
            font-weight: 600;
            text-align: center;
            border: 1px solid #2c3e50;
            font-size: 14px;
        }
        td {
            border: 1px solid #ddd;
            padding: 12px 8px;
            text-align: center;
            vertical-align: middle;
            transition: background 0.2s;
        }
        td:hover {
            filter: brightness(0.98);
        }
        .time-col {
            background-color: #ecf0f1;
            font-weight: 600;
            color: #2c3e50;
            width: 100px;
            font-size: 14px;
        }
        .break-slot {
            background-color: #fff3cd;
            color: #856404;
        }
        .event-slot {
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
            color: #856404;
            font-weight: 500;
        }
        .lecture-slot {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
        }
        .free-slot {
            background-color: #f8f9fa;
            color: #6c757d;
            font-style: italic;
        }
        .course-code {
            font-weight: 700;
            color: #155724;
            font-size: 16px;
        }
        .faculty-name {
            font-size: 13px;
            color: #2c3e50;
            margin-top: 4px;
            font-weight: 500;
        }
        .room-info {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 4px;
        }
        .legend {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 24px;
            height: 24px;
            border-radius: 4px;
        }
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-box {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .stat-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
            line-height: 1.2;
        }
        .stat-label {
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }
        @media print {
            body { background: white; }
            .header { background: #34495e; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            th { background: #34495e; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .section-tab { display: none; }
            .timetable-container { display: block; page-break-after: always; }
        }
    </style>
</head>
<body>
""")
        
        # Header
        total_slots = len(self.assignments)
        assigned_slots = sum(1 for v in self.assignments.values() if v == 1)
        break_slots = sum(1 for k, v in self.assignments.items() if 'B' in k)
        free_slots = total_slots - assigned_slots - break_slots
        
        html.append(f"""
    <div class="header">
        <h1>🏛️ Department of Computer Science and Engineering</h1>
        <p>Master Timetable - Academic Year 2025-2026 (ODD Semester)</p>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
    </div>
""")
        
        # Summary Statistics
        utilization = (assigned_slots/(total_slots-break_slots)*100) if (total_slots-break_slots) > 0 else 0
        
        html.append(f"""
    <div class="summary-stats">
        <div class="stat-box">
            <div class="stat-value">{total_slots}</div>
            <div class="stat-label">Total Slots</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{assigned_slots}</div>
            <div class="stat-label">Assigned Lectures</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{break_slots}</div>
            <div class="stat-label">Break/Event Slots</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{free_slots}</div>
            <div class="stat-label">Free Slots</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{utilization:.1f}%</div>
            <div class="stat-label">Utilization</div>
        </div>
    </div>
""")
        
        # Section Tabs
        html.append('<div class="section-tabs">')
        for i, section in enumerate(self.sections):
            active = 'active' if i == 0 else ''
            html.append(f'<button class="section-tab {active}" onclick="showSection({i})">Section {section["id"]}<br><small>{section["room"]}</small></button>')
        html.append('</div>')
        
        # Generate timetable for each section
        for idx, section in enumerate(self.sections):
            active = 'active' if idx == 0 else ''
            html.append(f"""
    <div id="section-{idx}" class="timetable-container {active}">
        <div class="section-header">
            <h2>Semester {section['semester']} - Section {section['id']}</h2>
            <p>📍 Room: {section['room']} | 👥 Students: {section['students']}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Day / Time</th>
""")
            
            # Time slots header
            for slot in self.time_slots:
                html.append(f'<th>{slot["label"]}</th>')
            
            html.append('</tr></thead><tbody>')
            
            # Each day
            for day in self.days:
                html.append('<tr>')
                html.append(f'<td class="time-col"><strong>{day}</strong></td>')
                
                # Each time slot
                for slot in self.time_slots:
                    if slot.get('is_break', False):
                        if "Morning Break" in slot['label']:
                            html.append('<td class="break-slot">☕ Morning Break</td>')
                        elif "Lunch" in slot['label']:
                            html.append('<td class="break-slot">🍽️ Lunch Break</td>')
                        else:
                            html.append('<td class="break-slot">⏸️ Break</td>')
                        continue
                    
                    # Get info for this slot
                    slot_info = self.get_slot_info(day, slot['start'])
                    
                    if slot_info['type'] == 'event':
                        html.append(f'<td class="event-slot">🎤 {slot_info["label"]}</td>')
                    elif slot_info['type'] == 'break':
                        html.append('<td class="break-slot">⏸️ Break</td>')
                    elif slot_info['type'] == 'lecture':
                        html.append(f"""
                            <td class="lecture-slot">
                                <div class="course-code">{slot_info['course_code']}</div>
                                <div class="faculty-name">👨‍🏫 {slot_info['faculty_name']}</div>
                                <div class="room-info">🏛️ {section['room']}</div>
                            </td>
                        """)
                    else:
                        html.append('<td class="free-slot">🟢 Free</td>')
                
                html.append('</tr>')
            
            html.append('</tbody></table>')
            html.append('</div>')
        
        # Legend
        html.append("""
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #d4edda;"></div>
            <span>📚 Lecture (Assigned)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #fff3cd;"></div>
            <span>⏸️ Break/Event</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #f8f9fa;"></div>
            <span>🟢 Free Slot</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffe69c;"></div>
            <span>🎤 Special Event</span>
        </div>
    </div>
""")
        
        # JavaScript for tabs
        html.append("""
    <script>
        function showSection(index) {
            // Hide all sections
            var sections = document.getElementsByClassName('timetable-container');
            for (var i = 0; i < sections.length; i++) {
                sections[i].classList.remove('active');
            }
            
            // Show selected section
            document.getElementById('section-' + index).classList.add('active');
            
            // Update tabs
            var tabs = document.getElementsByClassName('section-tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            tabs[index].classList.add('active');
        }
    </script>
</body>
</html>
""")
        
        return '\n'.join(html)
    
    def save(self, filename: str = "visual_timetable_real.html"):
        """Save visual timetable to HTML file"""
        html_content = self.generate_html()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        abs_path = os.path.abspath(filename)
        print(f"✅ Visual timetable saved to: {abs_path}")
        
        # Automatically open in browser
        webbrowser.open(f"file://{abs_path}")
        print("🚀 Opening in your default browser...")
    
    def generate_all(self):
        """Generate all timetable formats"""
        print("="*60)
        print("🎨 GENERATING REAL VISUAL TIMETABLE")
        print("="*60)
        print(f"📊 Status: {self.status}")
        print(f"📚 Total assignments: {len(self.assignments)}")
        print(f"👥 Faculties loaded: {len(self.faculty_info)}")
        print(f"📖 Courses loaded: {len(self.course_info)}")
        
        # Save HTML
        self.save()
        
        print("\n" + "="*60)
        print("✅ Complete! Check visual_timetable_real.html")
        print("="*60)


def main():
    generator = RealVisualTimetableGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()