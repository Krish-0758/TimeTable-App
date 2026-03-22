# generate_constraints.py - Fixed version
import json
import os
from collections import defaultdict
from pathlib import Path
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define paths
OUTPUT_DIR = Path('output')

def load_json_file(filepath):
    """Load JSON file with error handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filepath} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def generate_faculty_constraints(faculty_data):
    """Generate constraints for each faculty member"""
    constraints = []
    
    # Adjust limits for overloaded faculty
    overload_adjustments = {
        'drsangeetha_v': 28,
        'drshilpa_s_chaudhari': 28,
        'drtn_r_kumar': 28,
        'dra_parkavi': 28,
        'drrajarajeswari_s': 24,
        'drjsangeetha': 24,
        'pradeep_kumar_d': 28,
        'darshana_a_naik': 28,
        'nandini_s_b': 28,
        'soumya_c_s': 28,
        'mamatha_a': 28
    }
    
    for faculty_id, faculty_info in faculty_data.items():
        if faculty_id.startswith('unknown_'):
            continue
        
        max_units = faculty_info.get('max_units', 18)
        
        if faculty_id in overload_adjustments:
            old_max = max_units
            max_units = overload_adjustments[faculty_id]
            print(f"Adjusting {faculty_info.get('name', faculty_id)}: {old_max} -> {max_units} units")
            
        constraint = {
            "constraint_id": f"FAC_{faculty_id}",
            "constraint_type": "faculty",
            "parameters": {
                "faculty_id": faculty_id,
                "name": faculty_info.get('name', ''),
                "designation": faculty_info.get('designation', ''),
                "max_units": max_units,
                "courses": []
            }
        }
        constraints.append(constraint)
    
    return constraints

def extract_course_ratios(course_code, course_ratios):
    """Extract weekly requirements for a course"""
    if course_code in course_ratios:
        ratios = course_ratios[course_code]
        return {
            "weekly_lectures": ratios.get('lectures_per_week', 0),
            "weekly_tutorials": ratios.get('tutorials_per_week', 0),
            "weekly_labs": ratios.get('labs_per_week', 0)
        }
    else:
        # Default values if course not found
        if 'LAB' in course_code.upper():
            return {
                "weekly_lectures": 0,
                "weekly_tutorials": 0,
                "weekly_labs": 1
            }
        else:
            return {
                "weekly_lectures": 3,
                "weekly_tutorials": 0,
                "weekly_labs": 0
            }

def generate_course_constraints(course_mapping, course_ratios):
    """Generate constraints for each course in each section"""
    constraints = []
    faculty_courses = defaultdict(list)
    
    for section, courses in course_mapping.items():
        for course_code, course_info in courses.items():
            faculty_id = course_info.get('faculty_id', '')
            course_name = course_info.get('course_name', '')
            
            if not faculty_id:
                print(f"Warning: No faculty for {course_code} in {section}")
                continue
            
            requirements = extract_course_ratios(course_code, course_ratios)
            
            constraint = {
                "constraint_id": f"SUB_{course_code}_{section}",
                "constraint_type": "subject",
                "parameters": {
                    "course_id": course_code,
                    "course_code": course_code,
                    "course_name": course_name,
                    "section": section,
                    "weekly_lectures": requirements['weekly_lectures'],
                    "weekly_tutorials": requirements['weekly_tutorials'],
                    "weekly_labs": requirements['weekly_labs'],
                    "total_slots_per_week": (
                        requirements['weekly_lectures'] + 
                        requirements['weekly_tutorials'] + 
                        requirements['weekly_labs']
                    ),
                    "faculty_ids": [faculty_id],
                    "faculty_id": faculty_id
                }
            }
            constraints.append(constraint)
            
            if faculty_id:
                faculty_courses[faculty_id].append({
                    'course_code': course_code,
                    'section': section,
                    'requirements': requirements
                })
    
    return constraints, faculty_courses

def generate_lab_tutorial_rules(constraints):
    """Generate rules for labs and tutorials (2 consecutive slots)"""
    for constraint in constraints:
        if constraint['constraint_type'] == 'subject':
            params = constraint['parameters']
            weekly_tutorials = params.get('weekly_tutorials', 0)
            weekly_labs = params.get('weekly_labs', 0)
            
            if weekly_tutorials > 0 or weekly_labs > 0:
                constraint['parameters']['rules'] = {
                    "tutorial_rule": {
                        "type": "consecutive_slots",
                        "duration_slots": 2,
                        "units_per_session": 2,
                        "count": weekly_tutorials
                    } if weekly_tutorials > 0 else None,
                    "lab_rule": {
                        "type": "consecutive_slots",
                        "duration_slots": 2,
                        "units_per_session": 2,
                        "count": weekly_labs
                    } if weekly_labs > 0 else None
                }
    
    return constraints

def validate_faculty_workload(faculty_constraints, faculty_courses):
    """Validate if faculty workload is within limits"""
    validation_results = []
    
    for faculty_constraint in faculty_constraints:
        faculty_id = faculty_constraint['parameters']['faculty_id']
        max_units = faculty_constraint['parameters']['max_units']
        
        courses = faculty_courses.get(faculty_id, [])
        total_units = 0
        course_details = []
        
        for course in courses:
            req = course['requirements']
            units = (
                req.get('weekly_lectures', 0) * 2 +
                req.get('weekly_tutorials', 0) * 2 +
                req.get('weekly_labs', 0) * 2
            )
            total_units += units
            course_details.append({
                'course_code': course['course_code'],
                'section': course['section'],
                'units': units
            })
        
        faculty_constraint['parameters']['calculated_workload'] = {
            'total_units': total_units,
            'max_units': max_units,
            'remaining_units': max_units - total_units,
            'is_within_limit': total_units <= max_units,
            'courses': course_details
        }
        
        validation_results.append({
            'faculty_id': faculty_id,
            'name': faculty_constraint['parameters']['name'],
            'designation': faculty_constraint['parameters']['designation'],
            'total_units': total_units,
            'max_units': max_units,
            'is_within_limit': total_units <= max_units,
            'shortfall': max_units - total_units if total_units <= max_units else 0,
            'excess': total_units - max_units if total_units > max_units else 0
        })
    
    return validation_results

def generate_timetable_constraints(course_mapping):
    """Generate additional timetable-specific constraints"""
    constraints = []
    
    fixed_events = {
        "Monday": {
            "15:35-16:30": {
                "event": "Industry Talk/Training",
                "sections": ["3A", "3B", "3C", "3D", "5A", "5B", "5C", "5D"]
            }
        },
        "Friday": {
            "13:45-14:40": {
                "event": "Proctor Meeting",
                "sections": ["3A", "3B", "3C", "3D", "5A", "5B", "5C", "5D"]
            }
        }
    }
    
    constraints.append({
        "constraint_id": "FIXED_EVENTS",
        "constraint_type": "fixed_slots",
        "parameters": {
            "events": fixed_events,
            "description": "Fixed events that occupy time slots across all sections"
        }
    })
    
    breaks = {
        "morning_break": {"start": "10:50", "end": "11:05", "duration_minutes": 15},
        "lunch_break": {"start": "12:55", "end": "13:45", "duration_minutes": 50}
    }
    
    constraints.append({
        "constraint_id": "BREAK_TIMES",
        "constraint_type": "fixed_breaks",
        "parameters": {
            "breaks": breaks,
            "description": "Fixed break times when no classes can be scheduled"
        }
    })
    
    return constraints

def generate_solver_config():
    """Generate solver configuration"""
    return {
        "solver_config": {
            "time_slots_per_day": 7,
            "days_per_week": 5,
            "total_time_slots": 35,
            "sections": ["3A", "3B", "3C", "3D", "5A", "5B", "5C", "5D"],
            "slot_duration_minutes": 55,
            "lunch_break": {"start": "12:55", "end": "13:45"},
            "morning_break": {"start": "10:50", "end": "11:05"},
            "units_per_slot": 2,
            "units_per_consecutive_slots": 2
        }
    }

def save_constraints(all_constraints, filename='all_constraints.json'):
    """Save all constraints to JSON file"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_constraints, f, indent=2, ensure_ascii=False)
    print(f"[OK] Constraints saved to {filepath}")

def main():
    print("Loading extracted JSON files...")
    
    faculty_data = load_json_file(OUTPUT_DIR / 'faculty_data.json')
    course_mapping = load_json_file(OUTPUT_DIR / 'course_mapping.json')
    course_ratios = load_json_file(OUTPUT_DIR / 'course_ratios.json')
    
    if not all([faculty_data, course_mapping, course_ratios]):
        print("Error: Missing required JSON files")
        return
    
    print("\nGenerating faculty constraints...")
    faculty_constraints = generate_faculty_constraints(faculty_data)
    print(f"Generated {len(faculty_constraints)} faculty constraints")
    
    print("\nGenerating course constraints...")
    course_constraints, faculty_courses = generate_course_constraints(course_mapping, course_ratios)
    print(f"Generated {len(course_constraints)} course constraints")
    
    print("\nAdding lab/tutorial rules...")
    course_constraints = generate_lab_tutorial_rules(course_constraints)
    
    print("\nValidating faculty workload...")
    validation_results = validate_faculty_workload(faculty_constraints, faculty_courses)
    
    print("\n" + "="*70)
    print("FACULTY WORKLOAD VALIDATION SUMMARY")
    print("="*70)
    
    overloaded = []
    for result in validation_results:
        status = "[OK]" if result['is_within_limit'] else "[WARN]"
        print(f"{status} {result['name']:40s} {result['designation']:25s} "
              f"Units: {result['total_units']:3d}/{result['max_units']:3d}")
        
        if not result['is_within_limit']:
            overloaded.append(result)
    
    if overloaded:
        print("\n" + "="*70)
        print("WARNING: Overloaded faculty members:")
        print("="*70)
        for result in overloaded:
            print(f"  - {result['name']}: {result['total_units']}/{result['max_units']} units "
                  f"(excess: {result['excess']} units)")
    
    print("\nGenerating timetable constraints...")
    timetable_constraints = generate_timetable_constraints(course_mapping)
    
    print("\nGenerating solver configuration...")
    solver_config = generate_solver_config()
    
    # Filter course constraints to only include sections we're solving for
    active_sections = set(solver_config['solver_config']['sections'])
    filtered_course_constraints = [
        c for c in course_constraints 
        if c['parameters']['section'] in active_sections
    ]
    
    all_constraints = {
        "metadata": {
            "version": "1.0",
            "generated_date": "2026-03-22",
            "total_faculty": len(faculty_constraints),
            "total_courses": len(filtered_course_constraints),
            "total_sections": len(solver_config['solver_config']['sections'])
        },
        "faculty_constraints": faculty_constraints,
        "course_constraints": filtered_course_constraints,
        "timetable_constraints": timetable_constraints,
        "solver_config": solver_config,
        "workload_validation": validation_results
    }
    
    save_constraints(all_constraints, 'all_constraints.json')
    
    print("\n" + "="*70)
    print("CONSTRAINTS GENERATION SUMMARY")
    print("="*70)
    print(f"Faculty constraints: {len(faculty_constraints)}")
    print(f"Course constraints: {len(filtered_course_constraints)}")
    print(f"Timetable constraints: {len(timetable_constraints)}")
    print(f"Total constraints: {len(faculty_constraints) + len(filtered_course_constraints) + len(timetable_constraints)}")
    
    print("\nSection-wise course distribution:")
    sections = solver_config['solver_config']['sections']
    for section in sections:
        courses_in_section = [c for c in filtered_course_constraints 
                              if c['parameters']['section'] == section]
        print(f"  {section}: {len(courses_in_section)} courses")
    
    print("\n[OK] All constraints generated successfully!")

if __name__ == "__main__":
    main()