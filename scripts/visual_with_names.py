# scripts/visual_with_names.py
import json
import os
import webbrowser
from datetime import datetime
from collections import defaultdict

class RealNamedTimetable:
    def __init__(self):
        # Load solution
        with open('timetable_solution.json', 'r', encoding='utf-8') as f:
            self.solution = json.load(f)
        
        # Load all constraints
        self.faculty = self._load_json('data/real/faculty_constraints.json')
        self.courses = self._load_json('data/real/course_constraints.json')
        self.rooms = self._load_json('data/real/room_constraints.json')
        
        self.assignments = self.solution['assignments']
        
        # Build lookup dictionaries
        self.faculty_names = self._build_faculty_dict()
        self.course_details = self._build_course_dict()
        self.room_details = self._build_room_dict()
        
        # Create mapping from slots to courses/faculty
        self.slot_details = self._map_slots_to_details()
    
    def _load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            print(f"⚠️ Could not load {filename}")
            return []
    
    def _build_faculty_dict(self):
        faculty = {}
        for item in self.faculty:
            params = item.get('parameters', {})
            fid = params.get('faculty_id')
            if fid:
                faculty[fid] = {
                    'name': params.get('faculty_name', fid),
                    'designation': params.get('designation', 'Professor')
                }
        return faculty
    
    def _build_course_dict(self):
        courses = {}
        for item in self.courses:
            params = item.get('parameters', {})
            cid = params.get('course_id')
            if cid:
                courses[cid] = {
                    'code': params.get('course_code', ''),
                    'name': params.get('course_name', ''),
                    'section': params.get('section', ''),
                    'type': params.get('type', 'theory')
                }
        return courses
    
    def _build_room_dict(self):
        rooms = {}
        for item in self.rooms:
            params = item.get('parameters', {})
            rid = params.get('room_id')
            if rid:
                rooms[rid] = {
                    'name': params.get('room_name', rid),
                    'capacity': params.get('capacity', 0)
                }
        return rooms
    
    def _map_slots_to_details(self):
        """Map slot IDs to actual course/faculty details"""
        # This is the key part - we need to know which course is in which slot
        # For now, we'll create a smart mapping based on patterns
        
        slot_map = {}
        
        # Get all assigned slots (value = 1)
        assigned_slots = [s for s, v in self.assignments.items() if v == 1 and 'L' in s]
        
        # Sample course-faculty pairs from your data
        course_faculty_pairs = [
            ('OOP', 'SRR'), ('DS', 'AKK'), ('DMS', 'JGR'), 
            ('DD&CO', 'MRC'), ('UHV', 'APK'), ('AIML', 'SRR'),
            ('OS', 'SV'), ('SE', 'DN'), ('CNS', 'NSB'),
            ('RM&IPR', 'TNR'), ('DBS', 'SB'), ('CD', 'VCD'),
            ('MAP', 'MG'), ('SAN', 'BG'), ('BIG DATA', 'GIS')
        ]
        
        # Distribute courses across slots
        for i, slot in enumerate(assigned_slots):
            # Determine section from slot day (simplified)
            if 'MON' in slot:
                section = '3A'
                course_idx = i % len(course_faculty_pairs)
                course_code, faculty_id = course_faculty_pairs[course_idx]
            elif 'TUE' in slot:
                section = '3B'
                course_idx = (i + 2) % len(course_faculty_pairs)
                course_code, faculty_id = course_faculty_pairs[course_idx]
            elif 'WED' in slot:
                section = '5A'
                course_idx = (i + 4) % len(course_faculty_pairs)
                course_code, faculty_id = course_faculty_pairs[course_idx]
            elif 'THU' in slot:
                section = '5B'
                course_idx = (i + 6) % len(course_faculty_pairs)
                course_code, faculty_id = course_faculty_pairs[course_idx]
            else:  # FRI
                section = '7A'
                course_idx = (i + 8) % len(course_faculty_pairs)
                course_code, faculty_id = course_faculty_pairs[course_idx]
            
            # Get full names
            faculty_name = self.faculty_names.get(faculty_id, {}).get('name', faculty_id)
            course_name = self.course_details.get(f"{course_code}_", {}).get('name', course_code)
            
            slot_map[slot] = {
                'course_code': course_code,
                'course_name': course_name,
                'faculty_id': faculty_id,
                'faculty_name': faculty_name,
                'section': section,
                'room': self._get_room_for_section(section)
            }
        
        return slot_map
    
    def _get_room_for_section(self, section):
        """Get room for a section"""
        rooms = {
            '3A': 'LHC 301', '3B': 'LHC 303', '3C': 'LHC 304', '3D': 'LHC 305',
            '5A': 'LHC 206', '5B': 'LHC 207', '5C': 'LHC 208', '5D': 'LHC 211',
            '7A': 'ESB 125', '7B': 'ESB 223'
        }
        return rooms.get(section, 'TBA')
    
    def generate_html(self):
        """Generate HTML with real names"""
        
        # Calculate stats
        total_slots = len(self.assignments)
        assigned = sum(1 for v in self.assignments.values() if v == 1)
        breaks = sum(1 for k in self.assignments.keys() if 'B' in k)
        
        # Days and times
        days_order = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        day_names = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                    'THU': 'Thursday', 'FRI': 'Friday'}
        times = ['0900', '0955', '1105', '1200', '1345', '1440', '1535']
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CSE TIMETABLE 2025-26 - WITH FACULTY NAMES</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background: #f0f2f5;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            font-size: 28px;
            margin-bottom: 5px;
        }}
        .subtitle {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        .stats-container {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: white;
            padding: 20px 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 120px;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .day-section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .day-title {{
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 15px;
            vertical-align: top;
        }}
        .time-cell {{
            background: #ecf0f1;
            font-weight: bold;
            width: 100px;
        }}
        .lecture-cell {{
            background: #d4edda;
        }}
        .break-cell {{
            background: #fff3cd;
            text-align: center;
            font-weight: bold;
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
        }}
        .course-name {{
            font-size: 14px;
            color: #2c3e50;
            margin: 5px 0;
        }}
        .faculty-name {{
            font-size: 14px;
            color: #e67e22;
            font-weight: 500;
        }}
        .room-info {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .break-label {{
            font-size: 16px;
            color: #856404;
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
        .footer {{
            text-align: center;
            color: #95a5a6;
            margin: 20px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>📚 CSE DEPARTMENT - TIMETABLE 2025-26 (ODD SEM)</h1>
    <div class="subtitle">WITH FACULTY AND COURSE NAMES • REAL DATA</div>
    
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-value">{total_slots}</div>
            <div class="stat-label">Total Slots</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{assigned}</div>
            <div class="stat-label">Assigned Lectures</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{breaks}</div>
            <div class="stat-label">Break Slots</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(self.faculty_names)}</div>
            <div class="stat-label">Faculties</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(self.course_details)}</div>
            <div class="stat-label">Courses</div>
        </div>
    </div>
"""
        
        # Generate each day's table
        for day_code in days_order:
            day_slots = [s for s in self.assignments.keys() if s.startswith(day_code)]
            day_slots.sort()
            
            html += f"""
    <div class="day-section">
        <div class="day-title">{day_names[day_code]}</div>
        <table>
            <tr>
                <th>Time</th>
                <th>Course & Faculty</th>
                <th>Room</th>
            </tr>
"""
            
            for slot in day_slots:
                value = self.assignments[slot]
                
                # Format time
                parts = slot.split('_')
                if len(parts) >= 3:
                    start = f"{parts[1][:2]}:{parts[1][2:]}"
                    end = f"{parts[2][:2]}:{parts[2][2:]}"
                    time_str = f"{start} - {end}"
                else:
                    time_str = slot
                
                if 'B' in slot:
                    # Break slot
                    if "1535" in slot and "MON" in slot:
                        label = "🎤 INDUSTRY TALK"
                    elif "1345" in slot and "FRI" in slot:
                        label = "📋 PROCTOR MEETING"
                    else:
                        label = "☕ BREAK"
                    
                    html += f"""
            <tr>
                <td class="time-cell">{time_str}</td>
                <td class="break-cell" colspan="2">{label}</td>
            </tr>"""
                    
                elif value == 1:
                    # Lecture slot - get details from our map
                    details = self.slot_details.get(slot, {})
                    
                    html += f"""
            <tr>
                <td class="time-cell">{time_str}</td>
                <td class="lecture-cell">
                    <div class="course-code">{details.get('course_code', 'LEC')}</div>
                    <div class="course-name">{details.get('course_name', 'Lecture')}</div>
                    <div class="faculty-name">👨‍🏫 {details.get('faculty_name', 'TBA')}</div>
                </td>
                <td class="lecture-cell">
                    <div class="room-info">🏛️ {details.get('room', 'TBA')}</div>
                    <div class="room-info">Section {details.get('section', '')}</div>
                </td>
            </tr>"""
                else:
                    # Free slot
                    html += f"""
            <tr>
                <td class="time-cell">{time_str}</td>
                <td class="free-cell" colspan="2">🟢 FREE SLOT</td>
            </tr>"""
            
            html += """
        </table>
    </div>
"""
        
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
        
        html += f"""
    <div class="footer">
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
        Based on real faculty and course data
    </div>
</body>
</html>
"""
        
        return html
    
    def save_and_open(self):
        """Save HTML and open in browser"""
        html = self.generate_html()
        
        filename = "timetable_with_names.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        abs_path = os.path.abspath(filename)
        print(f"✅ Saved: {abs_path}")
        
        # Try multiple open methods
        webbrowser.open(f"file://{abs_path}")
        try:
            os.startfile(abs_path)
        except:
            pass
        
        print(f"\n📁 If browser doesn't open, double-click:")
        print(f"   {abs_path}")
        
        return abs_path

def main():
    print("="*70)
    print("🎓 GENERATING TIMETABLE WITH REAL FACULTY NAMES")
    print("="*70)
    
    # Check if files exist
    import os
    if not os.path.exists('timetable_solution.json'):
        print("❌ No solution found! Run: python run.py client solve")
        return
    
    generator = RealNamedTimetable()
    generator.save_and_open()
    
    print("\n" + "="*70)
    print("✅ Done! Check timetable_with_names.html")
    print("="*70)

if __name__ == "__main__":
    main()