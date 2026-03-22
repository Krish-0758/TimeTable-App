import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Define paths
OUTPUT_DIR = Path('output')

class TimetableVisualizer:
    def __init__(self, solution_file='timetable_solution.json', constraints_file='all_constraints.json'):
        """Initialize visualizer with solution and constraints data"""
        self.solution = self.load_json(OUTPUT_DIR / solution_file)
        self.constraints = self.load_json(OUTPUT_DIR / constraints_file)
        self.time_slots = [
            "09:00-09:55", "09:55-10:50", "11:05-12:00", "12:00-12:55",
            "13:45-14:40", "14:40-15:35", "15:35-16:30"
        ]
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
    def load_json(self, filename):
        """Load JSON file with error handling"""
        try:
            if not filename.exists():
                print(f"Warning: {filename} not found")
                return None
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {filename} is not valid JSON")
            return None
    
    def calculate_faculty_workload(self):
        """
        Calculate faculty workload from solution.
        Each lecture slot = 2 units
        Each tutorial block (2 slots) = 2 units (counted once)
        Each lab block (2 slots) = 2 units (counted once)
        """
        if not self.solution or not self.constraints:
            return {}
        
        faculty_workload = {}
        
        # First, initialize from constraints
        for fc in self.constraints.get('faculty_constraints', []):
            params = fc.get('parameters', {})
            faculty_id = params.get('faculty_id', '')
            if faculty_id:
                faculty_workload[faculty_id] = {
                    'name': params.get('name', faculty_id.replace('_', ' ').title()),
                    'designation': params.get('designation', 'Assistant Professor'),
                    'max_units': params.get('max_units', 28),
                    'actual_units': 0,
                    'courses': set(),
                    'slot_count': 0,
                    'block_count': 0
                }
        
        # Also add any faculty IDs that appear in solution but not in constraints
        for section, days in self.solution.items():
            if not days:
                continue
            for day, slots in days.items():
                if not slots:
                    continue
                for slot, assignment in slots.items():
                    if assignment and assignment is not None:
                        faculty_id = assignment.get('faculty_id', '')
                        if faculty_id and faculty_id not in faculty_workload:
                            # Add missing faculty with default values
                            faculty_workload[faculty_id] = {
                                'name': faculty_id.replace('_', ' ').title(),
                                'designation': 'Assistant Professor',
                                'max_units': 28,
                                'actual_units': 0,
                                'courses': set(),
                                'slot_count': 0,
                                'block_count': 0
                            }
        
        # Track which slots belong to which blocks to avoid double-counting
        # First pass: Collect all assignments
        assignments = []
        for section, days in self.solution.items():
            if not days:
                continue
            for day, slots in days.items():
                if not slots:
                    continue
                for slot, assignment in slots.items():
                    if assignment and assignment is not None:
                        try:
                            slot_int = int(slot)
                        except (ValueError, TypeError):
                            continue
                        course_code = assignment.get('course_code', '')
                        faculty_id = assignment.get('faculty_id', '')
                        
                        if faculty_id:
                            assignments.append({
                                'section': section,
                                'day': day,
                                'slot': slot_int,
                                'course_code': course_code,
                                'faculty_id': faculty_id
                            })
        
        # Group assignments by (faculty, section, day)
        grouped = defaultdict(list)
        for a in assignments:
            key = (a['faculty_id'], a['section'], a['day'])
            grouped[key].append(a)
        
        # For each group, sort by slot and identify consecutive sequences
        for key, group in grouped.items():
            faculty_id, section, day = key
            group.sort(key=lambda x: x['slot'])
            
            # Identify consecutive slots of same course
            i = 0
            while i < len(group):
                current = group[i]
                course_code = current['course_code']
                slot = current['slot']
                
                # Check if this is part of a block (next slot is consecutive and same course)
                if i + 1 < len(group) and group[i+1]['slot'] == slot + 1 and group[i+1]['course_code'] == course_code:
                    # This is a 2-slot block (tutorial or lab)
                    # Count as 2 units for the block
                    faculty_workload[faculty_id]['actual_units'] += 2
                    faculty_workload[faculty_id]['block_count'] += 1
                    faculty_workload[faculty_id]['courses'].add(course_code)
                    # Skip the next slot since it's part of this block
                    i += 2
                else:
                    # This is a single lecture slot
                    faculty_workload[faculty_id]['actual_units'] += 2
                    faculty_workload[faculty_id]['slot_count'] += 1
                    faculty_workload[faculty_id]['courses'].add(course_code)
                    i += 1
        
        return faculty_workload
    
    def calculate_section_summary(self):
        """Calculate summary for each section"""
        if not self.solution:
            return {}
        
        section_summary = {}
        for section, days in self.solution.items():
            if not days:
                continue
            total_slots = 0
            filled_slots = 0
            
            for day, slots in days.items():
                if not slots:
                    continue
                for slot, assignment in slots.items():
                    total_slots += 1
                    if assignment and assignment is not None:
                        filled_slots += 1
            
            utilization = (filled_slots / total_slots * 100) if total_slots > 0 else 0
            
            section_summary[section] = {
                'total_slots': total_slots,
                'filled_slots': filled_slots,
                'utilization': utilization
            }
        
        return section_summary
    
    def generate_html(self, output_file='timetable.html'):
        """Generate HTML timetable with modern design"""
        
        faculty_workload = self.calculate_faculty_workload()
        section_summary = self.calculate_section_summary()
        
        # Calculate overall statistics
        total_filled = sum(s['filled_slots'] for s in section_summary.values())
        total_slots = sum(s['total_slots'] for s in section_summary.values())
        total_utilization = (total_filled / total_slots * 100) if total_slots > 0 else 0
        
        # Safe values for display
        num_sections = len(self.solution) if self.solution else 0
        num_faculty = len(faculty_workload)
        
        # Build faculty workload HTML
        faculty_html = ""
        if faculty_workload:
            for faculty_id, workload in sorted(faculty_workload.items(), key=lambda x: x[1]['actual_units'], reverse=True):
                actual = workload['actual_units']
                max_units = workload['max_units']
                percentage = (actual / max_units * 100) if max_units > 0 else 0
                
                fill_class = ""
                if percentage > 85:
                    fill_class = "danger"
                elif percentage > 70:
                    fill_class = "warning"
                
                total_sessions = workload['slot_count'] + workload['block_count']
                course_count = len(workload['courses'])
                
                faculty_html += f"""
                <div class="workload-item">
                    <h4>{workload['name']}</h4>
                    <div class="workload-bar-bg"><div class="workload-fill {fill_class}" style="width: {percentage}%"></div></div>
                    <div class="meta-stats">
                        <span>📚 {actual}/{max_units} units</span>
                        <span>{percentage:.1f}%</span>
                    </div>
                    <div class="meta-stats" style="margin-top: 6px;">
                        <span>📖 {course_count} courses</span>
                        <span>🎯 {total_sessions} sessions</span>
                    </div>
                </div>
"""
        else:
            faculty_html = '<div class="workload-item"><p>No faculty workload data available</p></div>'
        
        # Build section summary HTML
        section_html = ""
        if section_summary:
            for section, summary in sorted(section_summary.items()):
                utilization = summary['utilization']
                fill_class = "danger" if utilization > 90 else ("warning" if utilization > 75 else "")
                
                section_html += f"""
                <div class="workload-item">
                    <h4>Section {section}</h4>
                    <div class="workload-bar-bg"><div class="workload-fill {fill_class}" style="width: {utilization}%"></div></div>
                    <div class="meta-stats">
                        <span>📅 {summary['filled_slots']}/{summary['total_slots']} slots</span>
                        <span>{utilization:.1f}% filled</span>
                    </div>
                </div>
"""
        else:
            section_html = '<div class="workload-item"><p>No section data available</p></div>'
        
        # Build timetable data for JavaScript
        timetable_data_json = {}
        if self.solution and len(self.solution) > 0:
            for section, days in self.solution.items():
                if not days:
                    continue
                timetable_data_json[section] = {}
                for day in self.days:
                    timetable_data_json[section][day] = {}
                    day_data = days.get(day, {})
                    for slot_idx in range(len(self.time_slots)):
                        assignment = day_data.get(str(slot_idx))
                        if assignment and assignment is not None:
                            timetable_data_json[section][day][str(slot_idx)] = {
                                'course': assignment.get('course_code', ''),
                                'faculty': assignment.get('faculty_id', '').replace('_', ' ').title(),
                                'faculty_id': assignment.get('faculty_id', '')
                            }
                        else:
                            timetable_data_json[section][day][str(slot_idx)] = None
        
        # Build faculty names dict for JavaScript
        faculty_names_dict = {}
        for fid, data in faculty_workload.items():
            faculty_names_dict[fid] = data.get('name', fid.replace('_', ' ').title())
        
        # Generate the full HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>CSE Department | Smart Timetable AY 2025-2026</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f0f2f8;
            padding: 30px 24px;
            color: #1a2634;
        }}

        .main-container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .hero-card {{
            background: linear-gradient(125deg, #0b2b40 0%, #1c4e6f 100%);
            border-radius: 32px;
            padding: 28px 36px;
            margin-bottom: 32px;
            color: white;
            box-shadow: 0 12px 25px -12px rgba(0, 0, 0, 0.25);
        }}

        .hero-card h1 {{
            font-size: 1.9rem;
            font-weight: 600;
            letter-spacing: -0.3px;
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .hero-card .sub {{
            font-size: 0.95rem;
            opacity: 0.85;
            margin-top: 10px;
            border-left: 3px solid #ffcd7e;
            padding-left: 16px;
        }}

        .hero-meta {{
            margin-top: 18px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.85rem;
        }}

        .stats-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 36px;
        }}

        .stat-card {{
            background: white;
            border-radius: 28px;
            padding: 18px 24px;
            flex: 1 1 200px;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }}

        .stat-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 18px 30px -12px rgba(0, 0, 0, 0.12);
        }}

        .stat-card h4 {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            color: #4b6b8f;
            margin-bottom: 12px;
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: 800;
            color: #1e4663;
            line-height: 1;
        }}

        .section-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 28px;
            background: white;
            padding: 12px 20px;
            border-radius: 60px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
            border: 1px solid #e9edf2;
        }}

        .section-tab {{
            background: transparent;
            border: none;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 8px 20px;
            border-radius: 40px;
            cursor: pointer;
            transition: all 0.2s;
            color: #3a5a78;
        }}

        .section-tab.active {{
            background: #1e5a7d;
            color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}

        .section-tab:hover:not(.active) {{
            background: #eef2f7;
        }}

        .timetable-panel {{
            display: none;
            animation: fade 0.25s ease;
        }}

        .timetable-panel.active-panel {{
            display: block;
        }}

        @keyframes fade {{
            from {{ opacity: 0; transform: translateY(5px);}}
            to {{ opacity: 1; transform: translateY(0);}}
        }}

        .section-card {{
            background: white;
            border-radius: 28px;
            overflow: hidden;
            box-shadow: 0 12px 28px -8px rgba(0, 0, 0, 0.08);
            margin-bottom: 20px;
            border: 1px solid #eef2f8;
        }}

        .section-title-bar {{
            background: #f8fafd;
            padding: 18px 28px;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}

        .section-title-bar h2 {{
            font-size: 1.65rem;
            font-weight: 700;
            color: #1e3a5f;
            letter-spacing: -0.2px;
        }}

        .util-badge {{
            background: #e8f0fe;
            padding: 6px 14px;
            border-radius: 40px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #1e5a7d;
        }}

        .table-wrapper {{
            overflow-x: auto;
            padding: 0 0 8px 0;
        }}

        .timetable {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.8rem;
            min-width: 700px;
        }}

        .timetable th {{
            background: #f9fbfe;
            padding: 16px 8px;
            text-align: center;
            font-weight: 700;
            font-size: 0.85rem;
            color: #2c4c6e;
            border-bottom: 1px solid #e2edf2;
        }}

        .timetable td {{
            padding: 14px 8px;
            text-align: center;
            border-bottom: 1px solid #ecf1f5;
            vertical-align: middle;
        }}

        .time-slot {{
            background: #f4f7fc;
            font-weight: 600;
            color: #1c4e6f;
            font-size: 0.75rem;
            white-space: nowrap;
        }}

        .lecture-cell {{
            background: #fefef7;
        }}

        .event-cell {{
            background: #fff1e0;
            position: relative;
        }}

        .course-code {{
            font-weight: 700;
            color: #1c5985;
            font-size: 0.8rem;
            background: #eef3fc;
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            margin-bottom: 4px;
        }}

        .faculty-name {{
            font-size: 0.7rem;
            color: #5a6e7c;
            margin-top: 5px;
            letter-spacing: -0.2px;
        }}

        .empty-slot {{
            color: #b1c3d4;
            font-style: italic;
            font-size: 0.7rem;
        }}

        .insight-section {{
            margin-top: 48px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px;
        }}

        .insight-card {{
            background: white;
            border-radius: 28px;
            padding: 24px 20px;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.03);
            border: 1px solid #eef2f5;
        }}

        .insight-card h3 {{
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 18px;
            color: #1e4663;
            display: flex;
            align-items: center;
            gap: 10px;
            border-left: 4px solid #ffb45e;
            padding-left: 16px;
        }}

        .workload-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 16px;
            max-height: 500px;
            overflow-y: auto;
            padding-right: 8px;
        }}

        .workload-item {{
            background: #fafcff;
            border-radius: 20px;
            padding: 12px 16px;
            border: 1px solid #eef2fa;
            transition: all 0.1s;
        }}

        .workload-item h4 {{
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 8px;
            color: #1f5170;
        }}

        .workload-bar-bg {{
            background: #e2e8f0;
            height: 8px;
            border-radius: 12px;
            margin: 10px 0 6px;
            overflow: hidden;
        }}

        .workload-fill {{
            background: #3680b0;
            height: 100%;
            width: 0%;
            border-radius: 12px;
        }}

        .workload-fill.warning {{
            background: #e68a2e;
        }}

        .workload-fill.danger {{
            background: #c94f4f;
        }}

        .meta-stats {{
            font-size: 0.7rem;
            color: #5e727e;
            display: flex;
            justify-content: space-between;
        }}

        .footer {{
            margin-top: 48px;
            background: #eef2f6;
            border-radius: 24px;
            padding: 24px 28px;
            text-align: center;
            font-size: 0.75rem;
            color: #3d5a73;
        }}

        @media (max-width: 780px) {{
            body {{ padding: 16px; }}
            .hero-card {{ padding: 20px; }}
            .insight-section {{ grid-template-columns: 1fr; }}
            .section-nav {{ border-radius: 28px; overflow-x: auto; flex-wrap: nowrap; justify-content: flex-start; }}
        }}
    </style>
</head>
<body>
<div class="main-container">
    <div class="hero-card">
        <h1>📘 Computer Science & Engineering</h1>
        <div class="sub">Academic Year 2025-2026 · ODD Semester · Automated Timetable System</div>
        <div class="hero-meta">
            <span>📅 Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</span>
            <span>🎓 {num_sections} Sections | {total_filled} Classes</span>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card"><h4>Total Sections</h4><div class="stat-number">{num_sections}</div></div>
        <div class="stat-card"><h4>Total Classes</h4><div class="stat-number">{total_filled}</div></div>
        <div class="stat-card"><h4>Overall Utilization</h4><div class="stat-number">{total_utilization:.1f}%</div></div>
        <div class="stat-card"><h4>Faculty Members</h4><div class="stat-number">{num_faculty}</div></div>
    </div>
"""

        # Add tabs and panels if solution exists
        if self.solution and len(self.solution) > 0:
            html += '<div class="section-nav" id="sectionTabs"></div>\n'
            html += '<div id="panelsContainer"></div>\n'
        else:
            html += """
            <div class="section-card" style="padding: 40px; text-align: center;">
                <h3 style="color: #1e5a7d;">📋 No timetable data available</h3>
                <p style="margin-top: 16px;">Please run the timetable generation process first to create the solution file.</p>
                <p style="margin-top: 8px; font-size: 0.85rem;">Expected file: output/timetable_solution.json</p>
            </div>
            """
        
        # Add insights section
        html += f"""
    <div class="insight-section">
        <div class="insight-card">
            <h3>👨‍🏫 Faculty Workload Distribution</h3>
            <div class="workload-grid">
                {faculty_html}
            </div>
        </div>
        <div class="insight-card">
            <h3>📊 Section Utilization</h3>
            <div class="workload-grid">
                {section_html}
            </div>
        </div>
    </div>

    <div class="footer">
        <p>📖 Legend: Light background - Regular Classes | Orange tint - Special Events (Proctor Meeting)</p>
        <p>⏰ Morning Break: 10:50-11:05 | Lunch Break: 12:55-13:45</p>
        <p>🎯 Proctor Meeting: Friday 13:45-14:40</p>
        <p>Generated by Department Timetable System | © 2026 CSE Department</p>
    </div>
</div>

<script>
    const sectionsData = {json.dumps({k: {"filled": v['filled_slots'], "total": v['total_slots']} for k, v in section_summary.items()})};
"""

        # Add JavaScript data if solution exists
        if self.solution and len(self.solution) > 0:
            html += f"""
    const fullTimetable = {json.dumps(timetable_data_json)};
    const timeSlots = {json.dumps(self.time_slots)};
    const days = {json.dumps(self.days)};
    const facultyNames = {json.dumps(faculty_names_dict)};

    function renderCellContent(assignment, day, slotIdx) {{
        if (day === 'Friday' && slotIdx === 4) {{
            return '<div><span class="course-code" style="background:#ffe0b5;">⭐ Proctor Meeting</span></div>';
        }}
        if (!assignment) {{
            return '<div class="empty-slot">— Free —</div>';
        }}
        let facultyDisplay = assignment.faculty || facultyNames[assignment.faculty_id] || assignment.faculty_id;
        if (facultyDisplay && facultyDisplay.length > 22) facultyDisplay = facultyDisplay.substring(0, 19) + '...';
        return '<div><span class="course-code">' + assignment.course + '</span><div class="faculty-name">' + (facultyDisplay || '') + '</div></div>';
    }}

    function buildTimetableHTML(section) {{
        const data = fullTimetable[section];
        if (!data) return '<div class="section-card"><div class="section-title-bar"><h2>Section ' + section + '</h2></div><div class="table-wrapper"><p style="padding:20px;">No data available</p></div></div>';
        
        let rows = '';
        for (let sIdx = 0; sIdx < timeSlots.length; sIdx++) {{
            let slotDisplay = timeSlots[sIdx];
            if (sIdx === 1) slotDisplay += '\\n(ends at break)';
            else if (sIdx === 2) slotDisplay += '\\n(starts after break)';
            else if (sIdx === 3) slotDisplay += '\\n(ends at lunch)';
            else if (sIdx === 4) slotDisplay += '\\n(starts after lunch)';
            
            rows += '<tr>';
            rows += '<td class="time-slot" style="font-weight:600;">' + slotDisplay.replace(/\\n/g, '<br>') + '</td>';
            for (let d of days) {{
                const assignment = data[d] ? data[d][sIdx] : null;
                const isEvent = (d === 'Friday' && sIdx === 4);
                const cellClass = isEvent ? 'event-cell' : 'lecture-cell';
                rows += '<td class="' + cellClass + '">' + renderCellContent(assignment, d, sIdx) + '</td>';
            }}
            rows += '</tr>';
        }}
        
        const filled = sectionsData[section]?.filled || 0;
        const total = sectionsData[section]?.total || 0;
        const util = total > 0 ? ((filled/total)*100).toFixed(1) : 0;
        
        return '<div class="section-card">' +
                    '<div class="section-title-bar">' +
                        '<h2>📖 Section ' + section + '</h2>' +
                        '<div class="util-badge">Filled: ' + filled + '/' + total + ' · ' + util + '%</div>' +
                    '</div>' +
                    '<div class="table-wrapper">' +
                        '<table class="timetable">' +
                            '<thead><tr><th>Time</th><th>Monday</th><th>Tuesday</th><th>Wednesday</th><th>Thursday</th><th>Friday</th></tr></thead>' +
                            '<tbody>' + rows + '</tbody>' +
                        '</table>' +
                    '</div>' +
                '</div>';
    }}

    const sections = {json.dumps(sorted([s for s in self.solution.keys() if self.solution[s]]))};
    const tabContainer = document.getElementById('sectionTabs');
    const panelsDiv = document.getElementById('panelsContainer');
    
    if (tabContainer && panelsDiv && sections.length > 0) {{
        sections.forEach((sec, idx) => {{
            const btn = document.createElement('button');
            btn.innerText = 'Section ' + sec;
            btn.classList.add('section-tab');
            if (idx === 0) btn.classList.add('active');
            btn.onclick = () => {{
                document.querySelectorAll('.section-tab').forEach(t => t.classList.remove('active'));
                btn.classList.add('active');
                document.querySelectorAll('.timetable-panel').forEach(p => p.classList.remove('active-panel'));
                document.getElementById('panel-' + sec).classList.add('active-panel');
            }};
            tabContainer.appendChild(btn);
            
            const panelDiv = document.createElement('div');
            panelDiv.id = 'panel-' + sec;
            panelDiv.className = 'timetable-panel' + (idx === 0 ? ' active-panel' : '');
            panelDiv.innerHTML = buildTimetableHTML(sec);
            panelsDiv.appendChild(panelDiv);
        }});
    }}
</script>
"""
        else:
            html += "<script>console.log('No timetable data to display');</script>"
        
        html += """
</body>
</html>
"""
        
        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        filepath = OUTPUT_DIR / output_file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Timetable generated: {filepath}")
        return filepath


def main():
    visualizer = TimetableVisualizer('timetable_solution.json', 'all_constraints.json')
    output_file = visualizer.generate_html('timetable.html')
    
    try:
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(output_file)}')
        print(f"✓ Opened {output_file} in browser")
    except Exception as e:
        print(f"Please open {output_file} manually in your browser")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()