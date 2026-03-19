#!/usr/bin/env python
"""
Simple HTML Timetable Viewer - Guaranteed to open
"""

import json
import os
import webbrowser
from datetime import datetime

def create_simple_timetable():
    """Create a simple HTML timetable that will definitely open"""
    
    # Load the solution
    try:
        with open('timetable_solution.json', 'r', encoding='utf-8') as f:
            solution = json.load(f)
    except FileNotFoundError:
        print("❌ timetable_solution.json not found!")
        print("   Run: python run.py client solve first")
        return
    
    # Get assignments
    assignments = solution.get('assignments', {})
    
    # If it's the new enhanced format, extract differently
    if isinstance(assignments, dict) and any(isinstance(v, dict) for v in assignments.values()):
        # Enhanced format with course info
        enhanced = True
        slot_info = {}
        for slot_id, info in assignments.items():
            if isinstance(info, dict):
                slot_info[slot_id] = info
    else:
        # Old format with just 0/1
        enhanced = False
        slot_info = {k: {'value': v} for k, v in assignments.items()}
    
    # Calculate stats
    total_slots = len(slot_info)
    if enhanced:
        assigned = sum(1 for v in slot_info.values() if isinstance(v, dict) and 'course_code' in v)
    else:
        assigned = sum(1 for v in slot_info.values() if v.get('value') == 1)
    
    # Days and times
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    day_names = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                 'THU': 'Thursday', 'FRI': 'Friday'}
    times = ['0900', '0955', '1105', '1200', '1345', '1440', '1535']
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CSE Timetable - Generated Solution</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f0f2f5;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
        }}
        .status {{
            text-align: center;
            font-size: 18px;
            margin: 10px;
            padding: 10px;
            background: {'#d4edda' if solution.get('status') == 'feasible' else '#f8d7da'};
            border-radius: 5px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 20px;
        }}
        .stat-box {{
            background: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        .time-col {{
            background: #ecf0f1;
            font-weight: bold;
            width: 100px;
        }}
        .lecture {{
            background: #d4edda;
        }}
        .break {{
            background: #fff3cd;
            text-align: center;
        }}
        .free {{
            background: #f8f9fa;
            color: #6c757d;
        }}
        .course-code {{
            font-weight: bold;
            color: #155724;
            font-size: 16px;
        }}
        .faculty-name {{
            font-size: 12px;
            color: #2a5298;
        }}
        .section {{
            font-size: 11px;
            color: #666;
            margin-top: 3px;
        }}
        .footer {{
            text-align: center;
            margin: 20px;
            color: #7f8c8d;
        }}
        .enhanced-badge {{
            background: #2a5298;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
            margin: 10px;
        }}
    </style>
</head>
<body>
    <h1>🏛️ CSE Department - Generated Timetable</h1>
    <div class="status">
        Status: {solution.get('status', 'unknown').upper()}
        {f'<span class="enhanced-badge">ENHANCED MODE - WITH COURSE INFO</span>' if enhanced else ''}
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{total_slots}</div>
            <div>Total Slots</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{assigned}</div>
            <div>Assigned Lectures</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{len(slot_info) - assigned}</div>
            <div>Free/Break Slots</div>
        </div>
    </div>
"""
    
    # Create table for each day
    for day in days:
        html += f"""
    <h2>{day_names[day]}</h2>
    <table>
        <tr>
            <th>Time</th>
            <th>Slot</th>
            <th>Assignment</th>
        </tr>
"""
        # Sort times
        day_slots = [s for s in slot_info.keys() if s.startswith(day)]
        day_slots.sort()
        
        for slot in day_slots:
            info = slot_info[slot]
            
            # Format time
            parts = slot.split('_')
            if len(parts) >= 3:
                start = f"{parts[1][:2]}:{parts[1][2:]}"
                end = f"{parts[2][:2]}:{parts[2][2:]}"
                time_str = f"{start}-{end}"
            else:
                time_str = slot
            
            # Determine cell content and class
            if 'B' in slot:
                cell_class = "break"
                if "1535" in slot and "MON" in slot:
                    content = "🎤 INDUSTRY TALK"
                elif "1345" in slot and "FRI" in slot:
                    content = "📋 PROCTOR MEETING"
                else:
                    content = "⏸️ BREAK"
            elif enhanced and isinstance(info, dict) and 'course_code' in info:
                cell_class = "lecture"
                content = f"""
                    <div class="course-code">{info['course_code']}</div>
                    <div class="faculty-name">{info['faculty_name']}</div>
                    <div class="section">Section {info.get('section', 'N/A')}</div>
                """
            elif not enhanced and info.get('value') == 1:
                cell_class = "lecture"
                content = "📚 LECTURE"
            else:
                cell_class = "free"
                content = "🟢 FREE"
            
            html += f"""
        <tr>
            <td class="time-col">{time_str}</td>
            <td>{slot}</td>
            <td class="{cell_class}">{content}</td>
        </tr>"""
        
        html += """
    </table>
"""
    
    html += f"""
    <div class="footer">
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
    
    # Save the file
    filename = "timetable_view.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Get absolute path
    abs_path = os.path.abspath(filename)
    print(f"✅ Saved to: {abs_path}")
    
    # Open in browser
    webbrowser.open(f"file://{abs_path}")
    print("🚀 Opening in browser...")
    
    # Also try Windows-specific open
    try:
        os.startfile(abs_path)
    except:
        pass
    
    return abs_path

if __name__ == "__main__":
    print("="*60)
    print("📅 SIMPLE TIMETABLE VIEWER")
    print("="*60)
    create_simple_timetable()
    print("\n✅ Done! Check your browser.")
    print("="*60)