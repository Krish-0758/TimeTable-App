#!/usr/bin/env python
"""
Simple visual timetable that definitely opens in browser
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
    
    assignments = solution['assignments']
    
    # Calculate stats
    total = len(assignments)
    assigned = sum(1 for v in assignments.values() if v == 1)
    breaks = sum(1 for k in assignments.keys() if 'B' in k)
    
    # Days and times
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    day_names = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                 'THU': 'Thursday', 'FRI': 'Friday'}
    times = ['0900', '0955', '1105', '1200', '1345', '1440', '1535']
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CSE Timetable - REAL DATA</title>
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
        .stats {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 20px 0;
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
            text-align: center;
        }}
        .time-col {{
            background: #ecf0f1;
            font-weight: bold;
        }}
        .lecture {{
            background: #d4edda;
            color: #155724;
        }}
        .break {{
            background: #fff3cd;
            color: #856404;
        }}
        .free {{
            background: #f8f9fa;
            color: #6c757d;
        }}
        .footer {{
            text-align: center;
            margin: 20px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <h1>📚 CSE Department - REAL Timetable</h1>
    <h3 style="text-align: center;">Academic Year 2025-2026 (ODD Semester)</h3>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{total}</div>
            <div>Total Slots</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{assigned}</div>
            <div>Assigned Lectures</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{breaks}</div>
            <div>Break Slots</div>
        </div>
    </div>
"""
    
    # Create table for each day
    for day in days:
        html += f"""
    <h3>{day_names[day]}</h3>
    <table>
        <tr>
            <th>Time</th>
            <th>Slot</th>
            <th>Status</th>
        </tr>
"""
        # Sort times
        day_slots = [s for s in assignments.keys() if s.startswith(day)]
        day_slots.sort()
        
        for slot in day_slots:
            value = assignments[slot]
            if 'B' in slot:
                status = "BREAK"
                css = "break"
            elif value == 1:
                status = "LECTURE"
                css = "lecture"
            else:
                status = "FREE"
                css = "free"
            
            # Format time nicely
            parts = slot.split('_')
            if len(parts) >= 3:
                start = f"{parts[1][:2]}:{parts[1][2:]}"
                end = f"{parts[2][:2]}:{parts[2][2:]}"
                time_str = f"{start}-{end}"
            else:
                time_str = slot
            
            html += f"""
        <tr>
            <td class="time-col">{time_str}</td>
            <td>{slot}</td>
            <td class="{css}">{status}</td>
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
    filename = "timetable_simple.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Get absolute path
    abs_path = os.path.abspath(filename)
    print(f"✅ Saved to: {abs_path}")
    
    # Try multiple ways to open
    print("🚀 Attempting to open in browser...")
    
    # Method 1: webbrowser.open
    webbrowser.open(f"file://{abs_path}")
    
    # Method 2: os.startfile (Windows)
    try:
        os.startfile(abs_path)
        print("✅ Opened with os.startfile")
    except:
        pass
    
    print(f"\n📁 If browser doesn't open, open this file manually:")
    print(f"   {abs_path}")
    
    return abs_path

if __name__ == "__main__":
    print("="*60)
    print("🎨 SIMPLE VISUAL TIMETABLE")
    print("="*60)
    
    # Check if solution exists
    import os
    if not os.path.exists('timetable_solution.json'):
        print("❌ No solution found! Run: python run.py client solve")
    else:
        filepath = create_simple_timetable()
        print("\n✅ Done! Check your browser.")
    
    print("="*60)