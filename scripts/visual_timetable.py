#!/usr/bin/env python
"""
Generate beautiful visual timetables matching your Word document format
Creates HTML/CSS tables with proper section-wise views
"""

import json
from datetime import datetime
from typing import Dict, List, Any
import webbrowser
import os

class VisualTimetableGenerator:
    def __init__(self, solution_file: str = "timetable_solution.json"):
        """Initialize with solution file"""
        with open(solution_file, encoding='utf-8') as f:
            self.solution = json.load(f)
        
        self.assignments = self.solution['assignments']
        self.status = self.solution['status']
        
        # Define time slots (matching your Word document format)
        self.time_slots = [
            {"start": "09:00", "end": "09:55", "label": "9:00-9:55"},
            {"start": "09:55", "end": "10:50", "label": "9:55-10:50"},
            {"start": "BREAK", "end": "BREAK", "label": "Morning Break", "is_break": True},
            {"start": "11:05", "end": "12:00", "label": "11:05-12:00"},
            {"start": "12:00", "end": "12:55", "label": "12:00-12:55"},
            {"start": "LUNCH", "end": "LUNCH", "label": "Lunch Break", "is_break": True},
            {"start": "13:45", "end": "14:40", "label": "1:45-2:40"},
            {"start": "14:40", "end": "15:35", "label": "2:40-3:35"},
            {"start": "15:35", "end": "16:30", "label": "3:35-4:30"}
        ]
        
        # Define sections (from your master timetable)
        self.sections = [
            {"id": "3A", "room": "LHC 301", "semester": "III", "coordinator": "DR SUSHMA B(SB)"},
            {"id": "3B", "room": "LHC 303", "semester": "III", "coordinator": "DR SUSHMA B(SB)"},
            {"id": "3C", "room": "LHC 304", "semester": "III", "coordinator": "DR SUSHMA B(SB)"},
            {"id": "3D", "room": "LHC 305", "semester": "III", "coordinator": "DR SUSHMA B(SB)"},
            {"id": "5A", "room": "LHC 206", "semester": "V", "coordinator": "DR SANGEETHA J(SJ)"},
            {"id": "5B", "room": "LHC 207", "semester": "V", "coordinator": "DR SANGEETHA J(SJ)"},
            {"id": "5C", "room": "LHC 208", "semester": "V", "coordinator": "DR SANGEETHA J(SJ)"},
            {"id": "5D", "room": "LHC 211", "semester": "V", "coordinator": "DR SANGEETHA J(SJ)"},
            {"id": "7A", "room": "ESB 125", "semester": "VII", "coordinator": "DR. S. RAJARAJESWARI (SRR)"},
            {"id": "7B", "room": "ESB 223", "semester": "VII", "coordinator": "DR. S. RAJARAJESWARI (SRR)"},
        ]
        
        # Days of week
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.day_codes = {'Monday': 'MON', 'Tuesday': 'TUE', 'Wednesday': 'WED', 
                         'Thursday': 'THU', 'Friday': 'FRI'}
        
        # Faculty names mapping (from your data)
        self.faculty_names = {
            'RCA': 'Dr. China Appala Naidu',
            'SS': 'Dr. S.Seema',
            'MRM': 'Dr. Monica R. Mundada',
            'NAM': 'Prof. Nagabhushan A M',
            'SSC': 'Dr.Shilpa S Chaudhari',
            'TNR': 'Dr.T.N R. Kumar',
            'SRR': 'Dr.Rajarajeswari S',
            'SJ': 'Dr.J.Sangeetha',
            'APK': 'Dr.A Parkavi',
            'JGR': 'Dr.J Geetha',
            'DRB': 'Dr.Dayananda R B',
            'SV': 'Dr.Sangeetha V',
            'GIS': 'Dr.Ganeshayya I Shidaganti',
            'SB': 'Dr.Sushma B',
            'VGS': 'Veena GS',
            'MG': 'Dr.Mallegowda M',
            'CP': 'Dr.Chandrika Prasad',
            'DPK': 'Pradeep kumar D',
            'DN': 'Darshana A Naik',
            'JSM': 'Jamuna S Murthy',
            'NSB': 'Nandini S B',
            'SCS': 'Soumya C S',
            'ASB': 'Akshata S Bhayyar',
            'VCD': 'Vishwachetan D',
            'AKK': 'Akshata Kamath',
            'MA': 'Mamatha A',
            'PN': 'Pallavi N',
            'BG': 'Brunda',
            'US': 'Uzma Sulthana',
            'PK': 'Priya K',
            'MMC': 'Dr. Manjula M C',
        }
        
        # Course names mapping
        self.course_names = {
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
            'RMIPR': 'Research Methodology & IPR',
            'UHV': 'Universal Human Values',
            'AEC': 'Ability Enhancement Course',
            'FSD': 'Full Stack Development',
            'DT': 'Design Thinking',
            'PLC': 'Programming Language Course',
        }
        
        # Parse assignments to get section data
        self.section_assignments = self._parse_section_assignments()
    
    def _parse_section_assignments(self) -> Dict:
        """Parse assignments and try to infer section from slot patterns"""
        # This is a simplified version - in reality, you'd need course-to-section mapping
        # For now, we'll create a default mapping
        section_data = {}
        for section in self.sections:
            section_data[section['id']] = {}
            for day in self.days:
                section_data[section['id']][day] = {}
        
        return section_data
    
    def _get_course_info(self, slot_id: str) -> str:
        """Get course name from slot ID (simplified)"""
        # This would need actual course mapping
        # For now, return a placeholder
        if 'B' in slot_id:
            return "BREAK"
        
        # Try to extract course code from somewhere
        # In a real implementation, you'd have a mapping from slots to courses
        return "Lecture"
    
    def generate_html(self) -> str:
        """Generate beautiful HTML timetable"""
        html = []
        
        # CSS Styles
        html.append("""<!DOCTYPE html>
<html>
<head>
    <title>Master Timetable - CSE Department 2025-2026 (ODD Semester)</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        }
        .section-tab {
            display: inline-block;
            padding: 10px 20px;
            margin-right: 5px;
            background: #e0e0e0;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        .section-tab:hover {
            background: #d0d0d0;
        }
        .section-tab.active {
            background: #667eea;
            color: white;
        }
        .timetable-container {
            display: none;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .timetable-container.active {
            display: block;
        }
        .section-header {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 5px solid #667eea;
        }
        .section-header h2 {
            margin: 0;
            color: #333;
        }
        .section-header p {
            margin: 5px 0 0;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            font-weight: 600;
            text-align: center;
            border: 1px solid #5a6fd8;
        }
        td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: center;
            vertical-align: middle;
        }
        .time-col {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
            width: 100px;
        }
        .break-slot {
            background-color: #fff3e0;
            color: #e65100;
            font-style: italic;
        }
        .lecture-slot {
            background-color: #e8f5e8;
            color: #2e7d32;
        }
        .free-slot {
            background-color: #f5f5f5;
            color: #999;
        }
        .course-code {
            font-weight: 600;
            color: #1976d2;
        }
        .faculty-code {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .room-info {
            font-size: 0.85em;
            color: #888;
            margin-top: 5px;
        }
        .legend {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
        }
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 5px;
            vertical-align: middle;
        }
        .summary-stats {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .stat-box {
            display: inline-block;
            padding: 15px 25px;
            background: white;
            border-radius: 8px;
            margin: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
        @media print {
            body { background: white; }
            .header { background: #667eea; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            th { background: #667eea; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
    </style>
</head>
<body>
""")
        
        # Header
        html.append(f"""
    <div class="header">
        <h1>📚 Department of Computer Science and Engineering</h1>
        <p>Master Timetable - Academic Year 2025-2026 (ODD Semester)</p>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
""")
        
        # Summary Statistics
        total_slots = len(self.assignments)
        assigned_slots = sum(1 for v in self.assignments.values() if v == 1)
        break_slots = sum(1 for k, v in self.assignments.items() if 'B' in k and v == 0)
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
            <div class="stat-value">{utilization:.1f}%</div>
            <div class="stat-label">Utilization</div>
        </div>
    </div>
""")
        
        # Section Tabs
        html.append('<div class="section-tabs">')
        for i, section in enumerate(self.sections):
            active = 'active' if i == 0 else ''
            html.append(f'<div class="section-tab {active}" onclick="showSection({i})">{section["id"]}</div>')
        html.append('</div>')
        
        # Generate timetable for each section
        for idx, section in enumerate(self.sections):
            active = 'active' if idx == 0 else ''
            html.append(f"""
    <div id="section-{idx}" class="timetable-container {active}">
        <div class="section-header">
            <h2>Semester {section['semester']} - Section {section['id']}</h2>
            <p>Room: {section['room']} | Coordinator: {section['coordinator']}</p>
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
                html.append(f'<td class="time-col">{day}</td>')
                
                day_code = self.day_codes[day]
                
                # Each time slot
                for slot in self.time_slots:
                    if slot.get('is_break', False):
                        # Fixed break slot
                        html.append(f'<td class="break-slot">{slot["label"]}</td>')
                        continue
                    
                    # Find matching slot
                    slot_found = False
                    for slot_id, value in self.assignments.items():
                        if slot_id.startswith(day_code) and slot["start"] in slot_id:
                            if 'B' in slot_id:
                                # Break/event slot
                                if "Industry Talk" in slot_id or "15:35" in slot_id:
                                    html.append('<td class="break-slot">Industry Talk</td>')
                                elif "Proctor" in slot_id or "13:45" in slot_id:
                                    html.append('<td class="break-slot">Proctor Meeting</td>')
                                else:
                                    html.append('<td class="break-slot">Break</td>')
                            elif value == 1:
                                # Lecture slot
                                html.append("""
                                    <td class="lecture-slot">
                                        <div class="course-code">CS101</div>
                                        <div class="faculty-code">Dr. Smith</div>
                                        <div class="room-info">LHC 301</div>
                                    </td>
                                """)
                            else:
                                # Free slot
                                html.append('<td class="free-slot">Free</td>')
                            slot_found = True
                            break
                    
                    if not slot_found:
                        html.append('<td class="free-slot">Free</td>')
                
                html.append('</tr>')
            
            html.append('</tbody></table>')
            html.append('</div>')
        
        # Legend
        html.append("""
    <div class="legend">
        <div class="legend-item">
            <span class="legend-color" style="background: #e8f5e8;"></span>
            <span>Lecture</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #fff3e0;"></span>
            <span>Break/Event</span>
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #f5f5f5;"></span>
            <span>Free Slot</span>
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
    
    def save(self, filename: str = "visual_timetable.html"):
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
        print("🎨 GENERATING VISUAL TIMETABLE")
        print("="*60)
        print(f"Status: {self.status}")
        print(f"Total assignments: {len(self.assignments)}")
        
        # Save HTML
        self.save()
        
        print("\n" + "="*60)
        print("✅ Complete! Check visual_timetable.html")
        print("="*60)


def main():
    generator = VisualTimetableGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()


