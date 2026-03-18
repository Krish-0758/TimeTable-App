# scripts/enhanced_timetable_viewer.py
"""
Beautiful HTML viewer for enhanced timetable output
This will definitely open in your browser
"""

import json
import os
import webbrowser
from datetime import datetime
from collections import defaultdict

def create_enhanced_viewer():
    """Create a beautiful HTML timetable from enhanced solution"""
    
    # Load the solution
    try:
        with open('timetable_solution.json', 'r', encoding='utf-8') as f:
            solution = json.load(f)
    except FileNotFoundError:
        print("❌ timetable_solution.json not found!")
        print("   Run: python run.py client solve first")
        return
    
    # Check if it's enhanced format
    assignments = solution.get('assignments', {})
    is_enhanced = False
    if assignments and isinstance(next(iter(assignments.values())), dict):
        is_enhanced = True
    
    # Days and time slots
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    day_names = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                 'THU': 'Thursday', 'FRI': 'Friday'}
    
    time_slots = [
        {'start': '0900', 'end': '0955', 'label': '9:00-9:55'},
        {'start': '0955', 'end': '1050', 'label': '9:55-10:50'},
        {'start': 'BREAK', 'label': 'Morning Break', 'is_break': True},
        {'start': '1105', 'end': '1200', 'label': '11:05-12:00'},
        {'start': '1200', 'end': '1255', 'label': '12:00-12:55'},
        {'start': 'LUNCH', 'label': 'Lunch Break', 'is_break': True},
        {'start': '1345', 'end': '1440', 'label': '1:45-2:40'},
        {'start': '1440', 'end': '1535', 'label': '2:40-3:35'},
        {'start': '1535', 'end': '1630', 'label': '3:35-4:30'},
    ]
    
    # Calculate statistics
    if is_enhanced:
        # Group by section
        section_assignments = defaultdict(list)
        faculty_assignments = defaultdict(list)
        course_assignments = defaultdict(list)
        
        for slot_id, info in assignments.items():
            if isinstance(info, dict):
                section = info.get('section', 'Unknown')
                faculty = info.get('faculty_id', 'Unknown')
                course = info.get('course_id', 'Unknown')
                
                section_assignments[section].append(info)
                faculty_assignments[faculty].append(info)
                course_assignments[course].append(info)
        
        stats = {
            'total_slots': len(assignments),
            'assigned': len([v for v in assignments.values() if isinstance(v, dict)]),
            'sections': len(section_assignments),
            'faculties': len(faculty_assignments),
            'courses': len(course_assignments)
        }
    else:
        stats = {
            'total_slots': len(assignments),
            'assigned': sum(1 for v in assignments.values() if v == 1),
            'sections': 0,
            'faculties': 0,
            'courses': 0
        }
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CSE Department - Enhanced Timetable</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 20px;
            background: #f0f2f5;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px;
        }}
        .feasible {{
            background: #d4edda;
            color: #155724;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #2a5298;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .section-tabs {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
            justify-content: center;
        }}
        .section-tab {{
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        .section-tab:hover {{
            background: #2a5298;
            color: white;
            transform: translateY(-2px);
        }}
        .section-tab.active {{
            background: #2a5298;
            color: white;
        }}
        .timetable-container {{
            display: none;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .timetable-container.active {{
            display: block;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: center;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 12px;
            vertical-align: top;
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
        }}
        .special-cell {{
            background: #f8d7da;
            text-align: center;
            font-weight: bold;
        }}
        .course-code {{
            font-size: 16px;
            font-weight: bold;
            color: #155724;
        }}
        .faculty-name {{
            font-size: 13px;
            color: #2a5298;
            margin: 5px 0;
        }}
        .section-info {{
            font-size: 12px;
            color: #666;
        }}
        .footer {{
            text-align: center;
            margin: 20px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ CSE Department - Timetable Generator</h1>
        <p>Academic Year 2025-2026 (ODD Semester)</p>
        <div class="status-badge feasible">Status: {solution.get('status', 'unknown').upper()}</div>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{stats['total_slots']}</div>
            <div class="stat-label">Total Slots</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['assigned']}</div>
            <div class="stat-label">Assigned Lectures</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('sections', 0)}</div>
            <div class="stat-label">Sections</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('faculties', 0)}</div>
            <div class="stat-label">Faculties</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('courses', 0)}</div>
            <div class="stat-label">Courses</div>
        </div>
    </div>
"""
    
    if is_enhanced:
        # Section tabs
        sections = sorted(section_assignments.keys())
        html += '<div class="section-tabs">'
        for i, section in enumerate(sections):
            active = 'active' if i == 0 else ''
            html += f'<button class="section-tab {active}" onclick="showSection({i})">Section {section}</button>'
        html += '</div>'
        
        # Create timetable for each section
        for idx, section in enumerate(sections):
            active = 'active' if idx == 0 else ''
            html += f"""
    <div id="section-{idx}" class="timetable-container {active}">
        <h2>Section {section}</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
"""
            for day in days:
                html += f'<th>{day_names[day]}</th>'
            html += '</tr></thead><tbody>'
            
            # For each time slot
            for slot in time_slots:
                if slot.get('is_break', False):
                    html += f'<tr><td class="time-col break-cell">{slot["label"]}</td>'
                    for _ in days:
                        html += f'<td class="break-cell">{slot["label"]}</td>'
                    html += '</tr>'
                else:
                    html += f'<tr><td class="time-col">{slot["label"]}</td>'
                    
                    for day in days:
                        # Find assignment for this day and time
                        slot_id = f"{day}_{slot['start']}_{slot['end']}_L"
                        assignment = assignments.get(slot_id)
                        
                        if assignment and isinstance(assignment, dict):
                            # Check if this assignment belongs to current section
                            if assignment.get('section') == section:
                                html += f"""
                                    <td class="lecture-cell">
                                        <div class="course-code">{assignment['course_code']}</div>
                                        <div class="faculty-name">{assignment['faculty_name']}</div>
                                    </td>"""
                            else:
                                html += '<td class="lecture-cell">Other Section</td>'
                        elif slot_id in assignments and assignments[slot_id] == 1:
                            html += '<td class="lecture-cell">📚 Lecture</td>'
                        else:
                            html += '<td class="free-cell">🟢 Free</td>'
                    
                    html += '</tr>'
            
            html += '</tbody></table>'
            
            # Add faculty list for this section
            section_faculties = set()
            section_courses = set()
            for info in section_assignments[section]:
                section_faculties.add(info.get('faculty_name', 'Unknown'))
                section_courses.add(info.get('course_code', 'Unknown'))
            
            html += f"""
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <p><strong>Section {section} Summary:</strong></p>
            <p>📚 Courses: {', '.join(sorted(section_courses))}</p>
            <p>👥 Faculty: {', '.join(sorted(section_faculties))}</p>
            <p>📊 Total Lectures: {len(section_assignments[section])}</p>
        </div>
    </div>
"""
        
        # Add JavaScript for tabs
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
"""
    else:
        # Simple view for non-enhanced format
        html += """
    <div class="timetable-container active">
        <h2>⚠️ Basic Format (No Course Info)</h2>
        <p>Your solution only has 0/1 values. Run the enhanced solver to see course details.</p>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Monday</th>
                    <th>Tuesday</th>
                    <th>Wednesday</th>
                    <th>Thursday</th>
                    <th>Friday</th>
                </tr>
            </thead>
            <tbody>
"""
        for slot in time_slots:
            if slot.get('is_break', False):
                html += f'<tr><td class="time-col break-cell">{slot["label"]}</td>'
                for _ in days:
                    html += f'<td class="break-cell">{slot["label"]}</td>'
                html += '</tr>'
            else:
                html += f'<tr><td class="time-col">{slot["label"]}</td>'
                for day in days:
                    slot_id = f"{day}_{slot['start']}_{slot['end']}_L"
                    value = assignments.get(slot_id, 0)
                    if value == 1:
                        html += '<td class="lecture-cell">📚 Lecture</td>'
                    else:
                        html += '<td class="free-cell">🟢 Free</td>'
                html += '</tr>'
        
        html += '</tbody></table></div>'
    
    html += """
    <div class="footer">
        <p>Generated by Timetable Generator v2.0.0 | CSE Department</p>
    </div>
</body>
</html>
"""
    
    # Save the file
    filename = "enhanced_timetable.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    abs_path = os.path.abspath(filename)
    print(f"✅ Saved to: {abs_path}")
    
    # Open in browser using multiple methods
    print("🚀 Opening in browser...")
    
    # Method 1: webbrowser
    webbrowser.open(f"file://{abs_path}")
    
    # Method 2: os.startfile (Windows)
    try:
        os.startfile(abs_path)
    except:
        pass
    
    return abs_path

if __name__ == "__main__":
    print("="*60)
    print("🎨 ENHANCED TIMETABLE VIEWER")
    print("="*60)
    create_enhanced_viewer()
    print("\n✅ Done! Check your browser.")
    print("="*60)