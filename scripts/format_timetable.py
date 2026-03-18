#!/usr/bin/env python
"""
Generate readable timetables from solution files
Creates section-wise timetables in a clean format
Windows-compatible version (no emojis)
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

class TimetableFormatter:
    def __init__(self, solution_file: str = "timetable_solution.json"):
        """Initialize with solution file"""
        with open(solution_file, encoding='utf-8') as f:
            self.solution = json.load(f)
        
        self.assignments = self.solution['assignments']
        self.status = self.solution['status']
        
        # Define time slots in order
        self.time_slots = [
            ("09:00", "09:55"),
            ("09:55", "10:50"),
            ("BREAK", "Morning Break"),
            ("11:05", "12:00"),
            ("12:00", "12:55"),
            ("LUNCH", "Lunch Break"),
            ("13:45", "14:40"),
            ("14:40", "15:35"),
            ("15:35", "16:30")
        ]
        
        # Map day codes to full names
        self.day_names = {
            'MON': 'Monday',
            'TUE': 'Tuesday', 
            'WED': 'Wednesday',
            'THU': 'Thursday',
            'FRI': 'Friday'
        }
        
        # Group assignments by section (we'll need to infer this from course IDs)
        self.section_timetables = defaultdict(lambda: defaultdict(dict))
        self._parse_assignments()
    
    def _parse_assignments(self):
        """Parse assignments and group by section and day"""
        for slot_id, value in self.assignments.items():
            if value == 1 or 'B' in slot_id:  # Include breaks
                # Parse slot_id format: DAY_START_END_TYPE
                parts = slot_id.split('_')
                if len(parts) >= 4:
                    day_code = parts[0]
                    start_time = parts[1]
                    end_time = parts[2]
                    slot_type = parts[3] if len(parts) > 3 else 'L'
                    
                    # Store in section timetables (using a default section for now)
                    # In future, we'll parse section from course data
                    self.section_timetables['ALL'][day_code][slot_id] = {
                        'start': f"{start_time[:2]}:{start_time[2:]}",
                        'end': f"{end_time[:2]}:{end_time[2:]}",
                        'type': 'Lecture' if slot_type == 'L' else 'Break',
                        'value': value
                    }
    
    def format_time_table(self) -> str:
        """Create a formatted timetable string (no emojis)"""
        if self.status != 'feasible':
            return f"No feasible solution found. Status: {self.status}"
        
        output = []
        output.append("="*80)
        output.append("GENERATED TIMETABLE - ACADEMIC YEAR 2025-2026 (ODD SEMESTER)")
        output.append("="*80)
        output.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append(f"Status: {self.status.upper()}")
        output.append("="*80)
        
        # Calculate statistics
        total_slots = len(self.assignments)
        assigned_slots = sum(1 for v in self.assignments.values() if v == 1)
        break_slots = sum(1 for k, v in self.assignments.items() if 'B' in k and v == 0)
        
        output.append(f"\nSUMMARY STATISTICS")
        output.append("-"*40)
        output.append(f"Total Slots: {total_slots}")
        output.append(f"Lecture Slots Assigned: {assigned_slots}")
        output.append(f"Break/Event Slots: {break_slots}")
        output.append(f"Utilization: {(assigned_slots/(total_slots-break_slots)*100):.1f}%")
        
        # Generate daily view
        output.append("\nDAILY TIMETABLE")
        output.append("="*80)
        
        for day_code, day_name in self.day_names.items():
            output.append(f"\n{day_name}")
            output.append("-"*60)
            
            # Table header
            output.append(f"{'Time':15} | {'Slot ID':30} | {'Status':10}")
            output.append("-"*60)
            
            # Get slots for this day
            day_slots = []
            for slot_id in self.assignments:
                if slot_id.startswith(day_code):
                    day_slots.append(slot_id)
            
            # Sort by time
            day_slots.sort()
            
            for slot_id in day_slots:
                value = self.assignments[slot_id]
                parts = slot_id.split('_')
                if len(parts) >= 4:
                    start = f"{parts[1][:2]}:{parts[1][2:]}"
                    end = f"{parts[2][:2]}:{parts[2][2:]}"
                    
                    # Determine status (no emojis)
                    if 'B' in slot_id:
                        status = "BREAK"
                    elif value == 1:
                        status = "CLASS"
                    else:
                        status = "FREE"
                    
                    output.append(f"{start}-{end:10} | {slot_id:30} | {status:10}")
            
            # Count for this day
            day_lectures = sum(1 for s in day_slots if 'L' in s and self.assignments[s] == 1)
            day_breaks = sum(1 for s in day_slots if 'B' in s)
            output.append("-"*60)
            output.append(f"Day Total: {day_lectures} lectures, {day_breaks} breaks")
        
        return "\n".join(output)
    
    def save_to_file(self, filename: str = "timetable_output.txt"):
        """Save formatted timetable to file (using utf-8 encoding)"""
        formatted = self.format_time_table()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(formatted)
        print(f"✅ Timetable saved to {filename}")
    
    def print_summary(self):
        """Print quick summary"""
        assigned = sum(1 for v in self.assignments.values() if v == 1)
        total = len(self.assignments)
        breaks = sum(1 for k, v in self.assignments.items() if 'B' in k)
        
        print("\n" + "="*50)
        print("QUICK SUMMARY")
        print("="*50)
        print(f"Total Slots: {total}")
        print(f"Lecture Slots: {total - breaks}")
        print(f"Assigned Lectures: {assigned}")
        print(f"Free Lecture Slots: {total - breaks - assigned}")
        print(f"Break Slots: {breaks}")
        print(f"Utilization: {(assigned/(total-breaks)*100):.1f}%")
        
        # Daily breakdown
        print("\nDaily Breakdown:")
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
            day_lectures = sum(1 for k, v in self.assignments.items() 
                             if k.startswith(day) and 'L' in k and v == 1)
            day_total = sum(1 for k in self.assignments.keys() 
                          if k.startswith(day) and 'L' in k)
            print(f"  {day}: {day_lectures}/{day_total} lectures")


def create_html_timetable():
    """Create an HTML version of the timetable"""
    with open('timetable_solution.json', encoding='utf-8') as f:
        solution = json.load(f)
    
    assignments = solution['assignments']
    
    html = []
    html.append("""<!DOCTYPE html>
<html>
<head>
    <title>Timetable Generator Output</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #555; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th { background-color: #4CAF50; color: white; padding: 10px; }
        td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .lecture { background-color: #e8f5e8; }
        .break { background-color: #fff3e0; }
        .free { background-color: #f5f5f5; }
        .summary { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Generated Timetable - AY 2025-2026 (ODD Semester)</h1>
""")
    
    # Summary statistics
    total_slots = len(assignments)
    assigned_slots = sum(1 for v in assignments.values() if v == 1)
    break_slots = sum(1 for k, v in assignments.items() if 'B' in k and v == 0)
    utilization = (assigned_slots/(total_slots-break_slots)*100) if (total_slots-break_slots) > 0 else 0
    
    html.append(f"""
    <div class="summary">
        <h3>Summary Statistics</h3>
        <p>Total Slots: {total_slots}</p>
        <p>Lecture Slots Assigned: {assigned_slots}</p>
        <p>Break/Event Slots: {break_slots}</p>
        <p>Utilization: {utilization:.1f}%</p>
    </div>
    """)
    
    # Group by day
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    day_names = {'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday', 
                 'THU': 'Thursday', 'FRI': 'Friday'}
    
    for day in days:
        html.append(f"<h2>{day_names[day]}</h2>")
        html.append("<table>")
        html.append("<tr><th>Time</th><th>Slot ID</th><th>Status</th></tr>")
        
        day_slots = [s for s in assignments.keys() if s.startswith(day)]
        day_slots.sort()
        
        for slot in day_slots:
            value = assignments[slot]
            
            if 'B' in slot:
                status = "BREAK"
                css_class = "break"
            elif value == 1:
                status = "CLASS"
                css_class = "lecture"
            else:
                status = "FREE"
                css_class = "free"
            
            parts = slot.split('_')
            if len(parts) >= 3:
                start = f"{parts[1][:2]}:{parts[1][2:]}"
                end = f"{parts[2][:2]}:{parts[2][2:]}"
                time_str = f"{start} - {end}"
            else:
                time_str = slot
            
            html.append(f"<tr class='{css_class}'><td>{time_str}</td><td>{slot}</td><td>{status}</td></tr>")
        
        html.append("</table>")
    
    html.append("</body></html>")
    
    with open('timetable_output.html', 'w', encoding='utf-8') as f:
        f.write("\n".join(html))
    
    print("✅ HTML timetable saved to timetable_output.html")


def main():
    """Main function"""
    print("="*60)
    print("TIMETABLE FORMATTER")
    print("="*60)
    
    # Create formatter
    formatter = TimetableFormatter()
    
    # Print summary
    formatter.print_summary()
    
    # Save formatted output
    formatter.save_to_file()
    
    # Create HTML version
    create_html_timetable()
    
    print("\n" + "="*60)
    print("✅ Complete! Check the generated files:")
    print("   - timetable_output.txt (plain text)")
    print("   - timetable_output.html (web view)")
    print("="*60)


if __name__ == "__main__":
    main()