# scripts/generate_structure.py

def generate_structure_from_template():
    """Generate structure.json from the master timetable"""
    
    # From your master timetable, we can see:
    structure = {
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "day_start_time": "09:00",
        "day_end_time": "16:30",
        "lecture_duration_minutes": 55,  # 9:00-9:55 is 55 mins
        "breaks": [
            {
                "label": "Morning Break",
                "start_time": "10:50",
                "end_time": "11:05"
            },
            {
                "label": "Lunch",
                "start_time": "12:50",
                "end_time": "13:45"
            }
        ]
    }
    
    with open("data/structure.json", 'w') as f:
        json.dump(structure, f, indent=2)
    
    return structure