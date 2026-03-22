# timetable_solver.py - FINAL VERSION with faculty gap soft constraint
from ortools.sat.python import cp_model
import json
from pathlib import Path
import sys
from collections import defaultdict

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUTPUT_DIR = Path('output')

class CompleteTimetableSolver:
    def __init__(self):
        self.load_data()
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.x = {}
        self.status = None
        self.objective_value = None
        self.faculty_teaching_vars = {}  # Track teaching per faculty per slot
        
    def load_data(self):
        """Load all constraints and build course data"""
        with open(OUTPUT_DIR / 'all_constraints.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Sections to generate
        self.sections = ['3A', '3B', '3C', '3D', '5A', '5B', '5C', '5D']
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.time_slots = list(range(7))  # 0-6
        
        # Blocked slots (special events)
        self.blocked_slots = {
            'Friday': [4]       # Proctor Meeting (13:45-14:40)
        }
        
        # Build course data
        self.course_data = {}
        self.course_list = []
        self.course_id_map = {}
        next_id = 1
        
        # Track total required slots
        self.total_required_slots = 0
        
        for cc in data['course_constraints']:
            params = cc['parameters']
            section = params['section']
            if section in self.sections:
                lectures = params['weekly_lectures']
                tutorials = params['weekly_tutorials']
                labs = params['weekly_labs']
                
                if lectures > 0 or tutorials > 0 or labs > 0:
                    if section not in self.course_data:
                        self.course_data[section] = []
                    
                    course_info = {
                        'code': params['course_code'],
                        'name': params['course_name'],
                        'faculty': params['faculty_id'],
                        'lectures': lectures,
                        'tutorials': tutorials,
                        'labs': labs,
                        'id': next_id
                    }
                    self.course_data[section].append(course_info)
                    self.course_list.append((section, params['course_code']))
                    self.course_id_map[(section, params['course_code'])] = next_id
                    
                    # Count actual slots needed (lectures + 2*tutorials + 2*labs)
                    actual_slots_needed = lectures + (tutorials * 2) + (labs * 2)
                    self.total_required_slots += actual_slots_needed
                    
                    next_id += 1
        
        self.num_courses = next_id - 1
        print(f"✅ Loaded {self.num_courses} courses")
        print(f"   Total required slots: {self.total_required_slots}")
        
        # Build faculty to courses mapping
        self.faculty_courses = defaultdict(list)
        for section in self.sections:
            for course in self.course_data.get(section, []):
                self.faculty_courses[course['faculty']].append({
                    'section': section,
                    'course_id': course['id'],
                    'code': course['code']
                })
        
        # Load faculty limits
        self.faculty_limits = {}
        for fc in data['faculty_constraints']:
            params = fc['parameters']
            self.faculty_limits[params['faculty_id']] = params['max_units']
    
    def create_variables(self):
        """Create decision variables"""
        print("📊 Creating decision variables...")
        self.x = {}
        for section in self.sections:
            self.x[section] = {}
            for day in self.days:
                self.x[section][day] = {}
                for slot in self.time_slots:
                    self.x[section][day][slot] = self.model.NewIntVar(
                        0, self.num_courses, f'x_{section}_{day}_{slot}'
                    )
        
        total_vars = len(self.sections) * len(self.days) * len(self.time_slots)
        print(f"   Created {total_vars} variables for {len(self.sections)} sections")
    
    def add_course_constraints(self):
        """Add constraints for each course"""
        print("📚 Adding course constraints...")
        
        for section in self.sections:
            for course in self.course_data.get(section, []):
                course_id = course['id']
                lectures = course['lectures']
                tutorials = course['tutorials']
                labs = course['labs']
                
                # Track assignments
                lecture_assignments = []      # Single slots
                tutorial_blocks = []          # 2-slot blocks
                lab_blocks = []               # 2-slot blocks
                
                for day in self.days:
                    day_lectures = []
                    day_tutorials = []
                    day_labs = []
                    
                    for slot in self.time_slots:
                        # Skip blocked slots
                        if slot in self.blocked_slots.get(day, []):
                            continue
                        
                        # Create assignment variable for this slot
                        is_assigned = self.model.NewBoolVar(f'assign_{section}_{course["code"]}_{day}_{slot}')
                        self.model.Add(self.x[section][day][slot] == course_id).OnlyEnforceIf(is_assigned)
                        self.model.Add(self.x[section][day][slot] != course_id).OnlyEnforceIf(is_assigned.Not())
                        
                        # Lectures: single slots
                        day_lectures.append(is_assigned)
                        
                        # Tutorials and Labs: need 2 consecutive slots
                        if slot < len(self.time_slots) - 1:
                            next_slot_blocked = (slot + 1) in self.blocked_slots.get(day, [])
                            if not next_slot_blocked:
                                # Variable for next slot assignment
                                next_assigned = self.model.NewBoolVar(f'next_{section}_{course["code"]}_{day}_{slot}')
                                self.model.Add(self.x[section][day][slot+1] == course_id).OnlyEnforceIf(next_assigned)
                                self.model.Add(self.x[section][day][slot+1] != course_id).OnlyEnforceIf(next_assigned.Not())
                                
                                # Tutorial block (2 slots = 1 tutorial session)
                                if tutorials > 0:
                                    is_tutorial_block = self.model.NewBoolVar(f'tutorial_{section}_{course["code"]}_{day}_{slot}')
                                    self.model.AddBoolAnd([is_assigned, next_assigned]).OnlyEnforceIf(is_tutorial_block)
                                    day_tutorials.append(is_tutorial_block)
                                
                                # Lab block (2 slots = 1 lab session)
                                if labs > 0:
                                    is_lab_block = self.model.NewBoolVar(f'lab_{section}_{course["code"]}_{day}_{slot}')
                                    self.model.AddBoolAnd([is_assigned, next_assigned]).OnlyEnforceIf(is_lab_block)
                                    day_labs.append(is_lab_block)
                    
                    # Per day constraints
                    self.model.Add(sum(day_lectures) <= 2)  # Max 2 lectures per day
                    
                    if tutorials > 0:
                        self.model.Add(sum(day_tutorials) <= 1)  # Max 1 tutorial block per day
                    
                    if labs > 0:
                        self.model.Add(sum(day_labs) <= 1)  # Max 1 lab block per day
                    
                    lecture_assignments.extend(day_lectures)
                    tutorial_blocks.extend(day_tutorials)
                    lab_blocks.extend(day_labs)
                
                # Weekly total constraints
                if lectures > 0:
                    self.model.Add(sum(lecture_assignments) == lectures)
                if tutorials > 0:
                    self.model.Add(sum(tutorial_blocks) == tutorials)
                if labs > 0:
                    self.model.Add(sum(lab_blocks) == labs)
    
    def add_faculty_constraints(self):
        """Same faculty can't teach multiple sections at same time"""
        print("👥 Adding faculty constraints...")
        
        # Build faculty to courses mapping
        faculty_courses = defaultdict(list)
        for section in self.sections:
            for course in self.course_data.get(section, []):
                faculty_courses[course['faculty']].append((section, course['id']))
        
        for faculty, courses in faculty_courses.items():
            for day in self.days:
                for slot in self.time_slots:
                    if slot in self.blocked_slots.get(day, []):
                        continue
                    
                    teaching_at_slot = []
                    for section, course_id in courses:
                        is_teaching = self.model.NewBoolVar(f'teach_{faculty}_{section}_{day}_{slot}')
                        self.model.Add(self.x[section][day][slot] == course_id).OnlyEnforceIf(is_teaching)
                        self.model.Add(self.x[section][day][slot] != course_id).OnlyEnforceIf(is_teaching.Not())
                        teaching_at_slot.append(is_teaching)
                    
                    if teaching_at_slot:
                        self.model.Add(sum(teaching_at_slot) <= 1)
    
    def add_faculty_gap_soft_constraint(self):
        """
        Soft constraint: Faculty should have a gap after each teaching session.
        After a lecture (1 slot) or a 2-hour block (tutorial/lab), the next slot should be free.
        This is implemented as a penalty to minimize back-to-back classes.
        """
        print("⏰ Adding faculty gap soft constraint (minimizing back-to-back classes)...")
        
        # Create teaching indicator variables for each faculty, day, slot
        self.faculty_teaching = defaultdict(lambda: defaultdict(dict))
        
        # Build faculty teaching indicators
        for faculty_id in self.faculty_limits.keys():
            for day in self.days:
                for slot in self.time_slots:
                    if slot in self.blocked_slots.get(day, []):
                        continue
                    self.faculty_teaching[faculty_id][day][slot] = self.model.NewBoolVar(
                        f'faculty_teaching_{faculty_id}_{day}_{slot}'
                    )
        
        # Link teaching indicators to actual assignments
        for faculty_id in self.faculty_limits.keys():
            for day in self.days:
                for slot in self.time_slots:
                    if slot in self.blocked_slots.get(day, []):
                        continue
                    
                    # Sum over all sections where this faculty teaches this slot
                    teaching_terms = []
                    for course_assignment in self.faculty_courses[faculty_id]:
                        section = course_assignment['section']
                        course_id = course_assignment['course_id']
                        
                        is_teaching = self.model.NewBoolVar(f'teach_ind_{faculty_id}_{section}_{day}_{slot}')
                        self.model.Add(self.x[section][day][slot] == course_id).OnlyEnforceIf(is_teaching)
                        self.model.Add(self.x[section][day][slot] != course_id).OnlyEnforceIf(is_teaching.Not())
                        teaching_terms.append(is_teaching)
                    
                    if teaching_terms:
                        self.model.Add(self.faculty_teaching[faculty_id][day][slot] == sum(teaching_terms))
                    else:
                        self.model.Add(self.faculty_teaching[faculty_id][day][slot] == 0)
        
        # Penalty variables for back-to-back teaching
        penalty_vars = []
        for faculty_id in self.faculty_limits.keys():
            for day in self.days:
                for slot in range(len(self.time_slots) - 1):
                    # Skip if either slot is blocked
                    if slot in self.blocked_slots.get(day, []) or (slot + 1) in self.blocked_slots.get(day, []):
                        continue
                    
                    # Check if faculty teaches in both current and next slot
                    teaches_current = self.faculty_teaching[faculty_id][day][slot]
                    teaches_next = self.faculty_teaching[faculty_id][day][slot + 1]
                    
                    # Variable for back-to-back violation
                    back_to_back = self.model.NewBoolVar(f'back_to_back_{faculty_id}_{day}_{slot}')
                    self.model.AddBoolAnd([teaches_current, teaches_next]).OnlyEnforceIf(back_to_back)
                    
                    penalty_vars.append(back_to_back)
        
        # Store penalty variables for objective
        self.back_to_back_penalties = penalty_vars
        if penalty_vars:
            print(f"   Created {len(penalty_vars)} penalty variables for back-to-back classes")
    
    def add_break_constraints(self):
        """
        Prevent classes from spanning breaks.
        This ONLY blocks 2-hour blocks that would cross the break times.
        Single lectures in slots adjacent to breaks are allowed.
        """
        print("⏰ Adding break constraints - Preventing blocks that span breaks...")
        
        for section in self.sections:
            for day in self.days:
                for course in self.course_data.get(section, []):
                    course_id = course['id']
                    
                    # Morning break (10:50-11:05) - Prevent block that spans slots 1 and 2
                    morning_span = self.model.NewBoolVar(f'morning_span_{section}_{day}_{course["code"]}')
                    self.model.Add(self.x[section][day][1] == course_id).OnlyEnforceIf(morning_span)
                    self.model.Add(self.x[section][day][2] == course_id).OnlyEnforceIf(morning_span)
                    self.model.Add(morning_span == 0)
                    
                    # Lunch break (12:55-13:45) - Prevent block that spans slots 3 and 4
                    lunch_span = self.model.NewBoolVar(f'lunch_span_{section}_{day}_{course["code"]}')
                    self.model.Add(self.x[section][day][3] == course_id).OnlyEnforceIf(lunch_span)
                    self.model.Add(self.x[section][day][4] == course_id).OnlyEnforceIf(lunch_span)
                    self.model.Add(lunch_span == 0)
    
    def add_special_events(self):
        """Block slots for special events"""
        print("🎯 Adding special event constraints...")
        
        for section in self.sections:
            # Friday slot 4 - Proctor Meeting (13:45-14:40)
            self.model.Add(self.x[section]['Friday'][4] == 0)
    
    def add_faculty_workload(self):
        """Add faculty workload constraints"""
        print("⚖️ Adding faculty workload constraints...")
        
        faculty_workload = defaultdict(int)
        for section in self.sections:
            for course in self.course_data.get(section, []):
                # Units: each lecture = 2, each tutorial block = 2, each lab block = 2
                units = (course['lectures'] * 2) + (course['tutorials'] * 2) + (course['labs'] * 2)
                faculty_workload[course['faculty']] += units
        
        print("\n   Faculty Workload Requirements:")
        for faculty, total_units in sorted(faculty_workload.items(), key=lambda x: x[1], reverse=True):
            max_units = self.faculty_limits.get(faculty, 18)
            status = "✓" if total_units <= max_units else "⚠️"
            print(f"     {faculty:35s} {total_units:3d} / {max_units:3d} units {status}")
        
        # Add constraints
        for faculty, total_units in faculty_workload.items():
            if faculty in self.faculty_limits:
                max_units = self.faculty_limits[faculty]
                self.model.Add(total_units <= max_units)
    
    def add_objective(self):
        """
        Maximize total assigned slots while minimizing back-to-back classes.
        Weight: 1.0 per assigned slot, -0.5 per back-to-back violation
        """
        print("🎯 Adding objective with back-to-back penalty...")
        
        total_assigned = 0
        for section in self.sections:
            for day in self.days:
                for slot in self.time_slots:
                    if slot in self.blocked_slots.get(day, []):
                        continue
                    is_filled = self.model.NewBoolVar(f'filled_{section}_{day}_{slot}')
                    self.model.Add(self.x[section][day][slot] > 0).OnlyEnforceIf(is_filled)
                    self.model.Add(self.x[section][day][slot] == 0).OnlyEnforceIf(is_filled.Not())
                    total_assigned += is_filled
        
        # Calculate total penalty for back-to-back classes
        total_penalty = 0
        if hasattr(self, 'back_to_back_penalties'):
            for penalty_var in self.back_to_back_penalties:
                total_penalty += penalty_var
        
        # Objective: Maximize assigned slots, minimize back-to-back violations
        # Each assigned slot = +1, each back-to-back violation = -0.5
        self.model.Maximize(total_assigned - total_penalty * 0.5)
    
    def solve(self, time_limit=120):
        """Solve the model"""
        print("\n" + "="*60)
        print("🚀 Starting Complete Timetable Solver")
        print("="*60)
        
        self.create_variables()
        self.add_break_constraints()
        self.add_course_constraints()
        self.add_faculty_constraints()
        self.add_faculty_gap_soft_constraint()  # NEW: Soft constraint for faculty gaps
        self.add_special_events()
        self.add_faculty_workload()
        self.add_objective()
        
        self.solver.parameters.max_time_in_seconds = time_limit
        self.solver.parameters.log_search_progress = True
        
        print("\n🔍 Solving...")
        self.status = self.solver.Solve(self.model)
        
        return self.status
    
    def extract_solution(self):
        """Extract solution from solver"""
        if self.status is None:
            print("❌ Solver not run yet!")
            return None
            
        if self.status != cp_model.OPTIMAL and self.status != cp_model.FEASIBLE:
            print(f"❌ No feasible solution found! Status: {self.status}")
            return None
        
        print(f"\n✅ Solution found!")
        print(f"   Objective value: {self.solver.ObjectiveValue()}")
        print(f"   Wall time: {self.solver.WallTime():.2f} seconds")
        
        # Count back-to-back violations in the solution
        if hasattr(self, 'back_to_back_penalties'):
            violations = sum(self.solver.Value(v) for v in self.back_to_back_penalties)
            print(f"   Back-to-back faculty classes: {violations}")
        
        solution = {}
        for section in self.sections:
            solution[section] = {}
            for day in self.days:
                solution[section][day] = {}
                for slot in self.time_slots:
                    course_id = self.solver.Value(self.x[section][day][slot])
                    if course_id > 0:
                        for course in self.course_data.get(section, []):
                            if course['id'] == course_id:
                                solution[section][day][slot] = {
                                    'course_code': course['code'],
                                    'course_name': course['name'],
                                    'faculty_id': course['faculty']
                                }
                                break
                    else:
                        solution[section][day][slot] = None
        
        return solution
    
    def save_solution(self, solution):
        """Save solution to JSON"""
        if not solution:
            return False
        
        serializable = {}
        for section, days_data in solution.items():
            serializable[section] = {}
            for day, slots in days_data.items():
                serializable[section][day] = {}
                for slot, assignment in slots.items():
                    if assignment:
                        serializable[section][day][str(slot)] = assignment
                    else:
                        serializable[section][day][str(slot)] = None
        
        with open(OUTPUT_DIR / 'timetable_solution.json', 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Solution saved to {OUTPUT_DIR}/timetable_solution.json")
        return True
    
    def print_statistics(self):
        """Print solver statistics safely"""
        print("\n" + "="*60)
        print("📊 SOLVER STATISTICS")
        print("="*60)
        try:
            status_name = self.solver.StatusName()
            print(f"   Status: {status_name}")
            print(f"   Objective value: {self.solver.ObjectiveValue()}")
            print(f"   Wall time: {self.solver.WallTime():.2f} seconds")
            print(f"   Conflicts: {self.solver.NumConflicts()}")
            print(f"   Branches: {self.solver.NumBranches()}")
        except Exception as e:
            status_text = 'OPTIMAL' if self.status == cp_model.OPTIMAL else 'FEASIBLE' if self.status == cp_model.FEASIBLE else 'UNKNOWN'
            print(f"   Status: {status_text}")
            print(f"   Objective value: {self.solver.ObjectiveValue()}")
            print(f"   Wall time: {self.solver.WallTime():.2f} seconds")
            print(f"   Note: Detailed statistics not available")

def main():
    print("\n" + "="*60)
    print("🎓 DEPARTMENT TIMETABLE GENERATOR")
    print("   Academic Year 2025-2026 (ODD Semester)")
    print("="*60 + "\n")
    
    solver = CompleteTimetableSolver()
    status = solver.solve(time_limit=120)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution = solver.extract_solution()
        if solution and solver.save_solution(solution):
            solver.print_statistics()
            print("\n" + "="*60)
            print("🎉 TIMETABLE GENERATED SUCCESSFULLY!")
            print("="*60)
            print("\n📋 Next steps:")
            print("   1. Run the visualizer to generate HTML:")
            print("      python scripts/visualize_timetable.py")
            print("\n   2. Open output/timetable.html in your browser")
            print("="*60)
        else:
            print("❌ Failed to save solution")
    else:
        print(f"\n❌ No solution found! Status code: {status}")
        print("   The problem may be infeasible. Check constraints.")

if __name__ == "__main__":
    main()