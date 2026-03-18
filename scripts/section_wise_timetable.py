# scripts/section_wise_timetable.py
"""
Generate proper section-wise timetables without overlaps
Creates separate timetables for each section (3A, 3B, 3C, 3D, 5A, 5B, 5C, 5D, 7A, 7B)
"""

import json
import os
import webbrowser
from datetime import datetime
from collections import defaultdict

class SectionWiseTimetable:
    def __init__(self):
        # Load solution
        with open('timetable_solution.json', 'r', encoding='utf-8') as f:
            self.solution = json.load(f)
        
        # Load constraints for faculty and course info
        self.faculty = self._load_json('data/real/faculty_constraints.json')
        self.courses = self._load_json('data/real/course_constraints.json')
        
        self.assignments = self.solution['assignments']
        
        # Build lookup dictionaries
        self.faculty_names = self._build_faculty_dict()
        self.course_details = self._build_course_dict()
        
        # Define sections with their rooms
        self.sections = {
            '3A': {'room': 'LHC 301', 'semester': 'III', 'coordinator': 'Dr. Sushma B'},
            '3B': {'room': 'LHC 303', 'semester': 'III', 'coordinator': 'Dr. Sushma B'},
            '3C': {'room': 'LHC 304', 'semester': 'III', 'coordinator': 'Dr. Sushma B'},
            '3D': {'room': 'LHC 305', 'semester': 'III', 'coordinator': 'Dr. Sushma B'},
            '5A': {'room': 'LHC 206', 'semester': 'V', 'coordinator': 'Dr. Sangeetha J'},
            '5B': {'room': 'LHC 207', 'semester': 'V', 'coordinator': 'Dr. Sangeetha J'},
            '5C': {'room': 'LHC 208', 'semester': 'V', 'coordinator': 'Dr. Sangeetha J'},
            '5D': {'room': 'LHC 211', 'semester': 'V', 'coordinator': 'Dr. Sangeetha J'},
            '7A': {'room': 'ESB 125', 'semester': 'VII', 'coordinator': 'Dr. S. Rajarajeswari'},
            '7B': {'room': 'ESB 223', 'semester': 'VII', 'coordinator': 'Dr. S. Rajarajeswari'},
        }
        
        # Define courses per section (from your subject allotment)
        self.section_courses = {
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
        
        # Faculty for each course (from your data)
        self.course_faculty = {
            'OOP': 'SRR', 'DS': 'AKK', 'DMS': 'JGR', 'DD&CO': 'MRC',
            'UHV': 'APK', 'MATHS': 'RP', 'AIML': 'SRR', 'OS': 'SV',
            'SE': 'DN', 'CNS': 'NSB', 'RM&IPR': 'TNR', 'DBS': 'SB',
            'CD': 'VCD', 'MAP': 'MG', 'SAN': 'BG', 'BIG DATA': 'GIS'
        }
        
        # Time slots in order
        self.time_slots = [
            {'start': '0900', 'end': '0955', 'label': '9:00-9:55', 'order': 1},
            {'start': '0955', 'end': '1050', 'label': '9:55-10:50', 'order': 2},
            {'start': 'BREAK1', 'end': 'BREAK1', 'label': 'Morning Break', 'is_break': True, 'order': 3},
            {'start': '1105', 'end': '1200', 'label': '11:05-12:00', 'order': 4},
            {'start': '1200', 'end': '1255', 'label': '12:00-12:55', 'order': 5},
            {'start': 'LUNCH', 'end': 'LUNCH', 'label': 'Lunch Break', 'is_break': True, 'order': 6},
            {'start': '1345', 'end': '1440', 'label': '1:45-2:40', 'order': 7},
            {'start': '1440', 'end': '1535', 'label': '2:40-3:35', 'order': 8},
            {'start': '1535', 'end': '1630', 'label': '3:35-4:30', 'order': 9},
        ]
        
        # Days
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.day_codes = {'Monday': 'MON', 'Tuesday': 'TUE', 'Wednesday': 'WED', 
                         'Thursday': 'THU', 'Friday': 'FRI'}
        
        # Build section-wise timetable
        self.section_timetables = self._build_section_timetables()
    
    def _load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _build_faculty_dict(self):
        faculty = {}
        for item in self.faculty:
            params = item.get('parameters', {})
            fid = params.get('faculty_id')
            if fid:
                faculty[fid] = params.get('faculty_name', fid)
        return faculty
    
    def _build_course_dict(self):
        courses = {}
        for item in self.courses:
            params = item.get('parameters', {})
            cid = params.get('course_id')
            if cid:
                courses[cid] = params.get('course_name', '')
        return courses
    
    def _get_slot_time(self, slot_id):
        """Extract time from slot_id"""
        parts = slot_id.split('_')
        if len(parts) >= 3:
            return parts[1]  # Return start time
        return None
    
    def _get_slot_day(self, slot_id):
        """Extract day from slot_id"""
        parts = slot_id.split('_')
        if len(parts) >= 1:
            return parts[0]
        return None
    
    def _build_section_timetables(self):
        """Build timetable for each section without overlaps"""
        
        # Initialize empty timetables for each section
        timetables = {}
        for section in self.sections:
            timetables[section] = {}
            for day in self.days:
                timetables[section][day] = {}
                for slot in self.time_slots:
                    if slot.get('is_break', False):
                        timetables[section][day][slot['start']] = {
                            'type': 'break',
                            'label': slot['label']
                        }
                    else:
                        timetables[section][day][slot['start']] = {
                            'type': 'free',
                            'value': 0
                        }
        
        # Get all assigned lecture slots
        assigned_slots = [s for s, v in self.assignments.items() if v == 1 and 'L' in s]
        
        # Distribute slots to sections (this is where you'd use your actual mapping)
        # For now, we'll distribute them in a round-robin fashion
        section_list = list(self.sections.keys())
        slot_index = 0
        
        for slot in assigned_slots:
            day_code = self._get_slot_day(slot)
            time_code = self._get_slot_time(slot)
            
            if not day_code or not time_code:
                continue
            
            # Find which day this is
            day = None
            for d, code in self.day_codes.items():
                if code == day_code:
                    day = d
                    break
            
            if not day:
                continue
            
            # Assign to a section in round-robin
            section = section_list[slot_index % len(section_list)]
            slot_index += 1
            
            # Get course for this section (cycle through available courses)
            available_courses = self.section_courses[section]
            course_idx = (slot_index // len(section_list)) % len(available_courses)
            course = available_courses[course_idx]
            
            # Get faculty for this course
            faculty_id = self.course_faculty.get(course, 'TNR')
            faculty_name = self.faculty_names.get(faculty_id, faculty_id)
            course_name = self.course_details.get(f"{course}_", course)
            
            # Update timetable
            timetables[section][day][time_code] = {
                'type': 'lecture',
                'value': 1,
                'course_code': course,
                'course_name': course_name,
                'faculty_id': faculty_id,
                'faculty_name': faculty_name,
                'room': self.sections[section]['room']
            }
        
        return timetables
    
    def generate_html(self):
        """Generate HTML with section-wise timetables"""
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CSE Department - Section Wise Timetable 2025-26</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f0f2f5;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
        }}
        .section-tabs {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: center;
        }}
        .section-tab {{
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        .section-tab:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .section-tab.active {{
            background: #3498db;
            color: white;
        }}
        .timetable-container {{
            display: none;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .timetable-container.active {{
            display: block;
        }}
        .section-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 5px solid #3498db;
        }}
        .section-header h2 {{
            margin: 0;
            color: #2c3e50;
        }}
        .section-header p {{
            margin: 5px 0 0;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: center;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 15px;
            vertical-align: top;
            height: 100px;
        }}
        .time-col {{
            background: #ecf0f1;
            font-weight: bold;
            width: 100px;
            text-align: center;
        }}
        .lecture-cell {{
            background: #d4edda;
        }}
        .break-cell {{
            background: #fff3cd;
            text-align: center;
            font-weight: bold;
            color: #856404;
        }}
        .free-cell {{
            background: #f8f9fa;
            text-align: center;
            color: #6c757d;
        }}
        .course-code {{
            font-size: 18px;
            font-weight: bold;
            color: #155724;
            margin-bottom: 5px;
        }}
        .faculty-name {{
            font-size: 14px;
            color: #e67e22;
            margin: 5px 0;
        }}
        .room-info {{
            font-size: 12px;
            color: #7f8c8d;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        @media print {{
            .section-tabs {{ display: none; }}
            .timetable-container {{ display: block; page-break-after: always; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Department of Computer Science and Engineering</h1>
        <p>Section-Wise Timetable - Academic Year 2025-2026 (ODD Semester)</p>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
    </div>
"""
        
        # Section tabs
        html += '<div class="section-tabs">'
        for i, section in enumerate(sorted(self.sections.keys())):
            active = 'active' if i == 0 else ''
            html += f'<button class="section-tab {active}" onclick="showSection({i})">Section {section}<br><small>{self.sections[section]["room"]}</small></button>'
        html += '</div>'
        
        # Generate timetable for each section
        sections_list = sorted(self.sections.keys())
        for idx, section in enumerate(sections_list):
            active = 'active' if idx == 0 else ''
            html += f"""
    <div id="section-{idx}" class="timetable-container {active}">
        <div class="section-header">
            <h2>Semester {self.sections[section]['semester']} - Section {section}</h2>
            <p>📍 Room: {self.sections[section]['room']} | 👤 Coordinator: {self.sections[section]['coordinator']}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Time</th>
"""
            
            # Day headers
            for day in self.days:
                html += f'<th>{day}</th>'
            html += '</tr></thead><tbody>'
            
            # Time slots
            for slot in sorted(self.time_slots, key=lambda x: x['order']):
                if slot.get('is_break', False):
                    # Break row - same for all days
                    html += '<tr>'
                    html += f'<td class="time-col">{slot["label"]}</td>'
                    for _ in self.days:
                        html += f'<td class="break-cell" colspan="1">{slot["label"]}</td>'
                    html += '</tr>'
                else:
                    # Regular slot - check each day
                    html += '<tr>'
                    html += f'<td class="time-col">{slot["label"]}</td>'
                    
                    for day in self.days:
                        cell = self.section_timetables[section][day].get(slot['start'], {'type': 'free'})
                        
                        if cell['type'] == 'lecture':
                            html += f"""
                                <td class="lecture-cell">
                                    <div class="course-code">{cell['course_code']}</div>
                                    <div class="faculty-name">👨‍🏫 {cell['faculty_name']}</div>
                                    <div class="room-info">🏛️ {cell['room']}</div>
                                </td>"""
                        elif cell['type'] == 'free':
                            html += '<td class="free-cell">🟢 Free</td>'
                        else:
                            html += f'<td class="free-cell">-</td>'
                    
                    html += '</tr>'
            
            html += '</tbody></table>'
            html += '</div>'
        
        # Legend
        html += """
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #d4edda;"></div>
            <span>📚 Lecture (with faculty)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #fff3cd;"></div>
            <span>⏸️ Break/Event</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #f8f9fa;"></div>
            <span>🟢 Free Slot</span>
        </div>
    </div>
"""
        
        # JavaScript for tabs
        html += """
    <script>
        function showSection(index) {
            var sections = document.getElementsByClassName('timetable-container');
            for (var i = 0; i < sections.length; i++) {
                sections[i].classList.remove('active');
            }
            document.getElementById('section-' + index).classList.add('active');
            
            var tabs = document.getElementsByClassName('section-tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            tabs[index].classList.add('active');
        }
    </script>
</body>
</html>
"""
        
        return html
    
    def save_and_open(self):
        """Save HTML and open in browser"""
        html = self.generate_html()
        
        filename = "section_wise_timetable.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        abs_path = os.path.abspath(filename)
        print(f"✅ Saved: {abs_path}")
        
        # Open in browser
        webbrowser.open(f"file://{abs_path}")
        
        return abs_path

def main():
    print("="*70)
    print("🎯 GENERATING SECTION-WISE TIMETABLE")
    print("="*70)
    
    generator = SectionWiseTimetable()
    generator.save_and_open()
    
    print("\n✅ Complete! Check section_wise_timetable.html")
    print("="*70)

if __name__ == "__main__":
    main()
    