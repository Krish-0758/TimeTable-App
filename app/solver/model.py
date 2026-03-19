"""
Enhanced solver model that assigns specific courses to slots
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from ortools.sat.python import cp_model

from app.constraints.schema import ConstraintBase

logger = logging.getLogger(__name__)


class EnhancedTimetableModel:
    """
    CP-SAT model that assigns actual courses to slots
    """
    
    def __init__(
        self,
        timetable_structure: Dict[str, List[Dict[str, Any]]],
        slot_ids: Dict[str, List[str]],
        constraints: List[ConstraintBase],
    ):
        self.model = cp_model.CpModel()
        self.timetable_structure = timetable_structure
        self.slot_ids = slot_ids
        self.constraints = constraints
        
        # Extract courses and faculties from constraints
        self.courses = self._extract_courses()
        self.faculties = self._extract_faculties()
        self.sections = self._extract_sections()
        
        # Create mapping dictionaries
        self.course_faculty_map = self._build_course_faculty_map()
        self.section_courses_map = self._build_section_courses_map()
        
        # Decision variables: assignment[faculty][course][slot] -> BoolVar
        self.assignment_vars: Dict[str, Dict[str, Dict[str, cp_model.IntVar]]] = {}
        
        # Track which slots are used (for objective)
        self.slot_used_vars: Dict[str, cp_model.IntVar] = {}
        
        self._create_variables()
        self._add_constraints()
        self._set_objective()
    
    def _extract_courses(self) -> Dict[str, Dict]:
        """Extract course information from constraints including lab/tutorial hours"""
        courses = {}
        for constraint in self.constraints:
            if constraint.constraint_type == "subject":
                params = constraint.parameters
                course_id = params.get('course_id') or params.get('subject_code')
                if course_id:
                    courses[course_id] = {
                        'id': course_id,
                        'code': params.get('course_code', ''),
                        'name': params.get('course_name', ''),
                        'section': params.get('section', 'COMMON'),
                        'type': params.get('type', 'theory'),
                        'weekly_lectures': params.get('weekly_lectures', 3),
                        'weekly_tutorials': params.get('weekly_tutorials', 0),
                        'weekly_labs': params.get('weekly_labs', 0),
                        'requires_lab': params.get('requires_lab', False),
                        'faculty_ids': params.get('faculty_ids', [])
                    }
        return courses
    
    def _extract_faculties(self) -> Dict[str, Dict]:
        """Extract faculty information from constraints"""
        faculties = {}
        for constraint in self.constraints:
            if constraint.constraint_type == "faculty":
                params = constraint.parameters
                faculty_id = params.get('faculty_id')
                if faculty_id:
                    faculties[faculty_id] = {
                        'id': faculty_id,
                        'name': params.get('faculty_name', faculty_id),
                        'max_hours': params.get('max_hours_per_week', 20),
                        'available_days': params.get('available_days', 
                                                     ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
                    }
        return faculties
    
    def _extract_sections(self) -> List[str]:
        """Extract all sections from courses"""
        sections = set()
        for course in self.courses.values():
            sections.add(course['section'])
        return list(sections)
    
    def _build_course_faculty_map(self) -> Dict[str, List[str]]:
        """Map each course to faculty who can teach it"""
        course_faculty = {}
        for course_id, course in self.courses.items():
            course_faculty[course_id] = course.get('faculty_ids', [])
        return course_faculty
    
    def _build_section_courses_map(self) -> Dict[str, List[str]]:
        """Map each section to its courses"""
        section_courses = {}
        for course_id, course in self.courses.items():
            section = course['section']
            if section not in section_courses:
                section_courses[section] = []
            section_courses[section].append(course_id)
        return section_courses
    
    def _create_variables(self):
        """
        Create decision variables:
        - assignment[faculty_id][course_id][slot_id] = 1 if this faculty teaches this course in this slot
        - slot_used[slot_id] = 1 if any course is assigned to this slot
        """
        
        # Get all slot IDs
        all_slots = []
        for day_slots in self.slot_ids.values():
            all_slots.extend(day_slots)
        
        # Create assignment variables for each possible combination
        for faculty_id in self.faculties:
            self.assignment_vars[faculty_id] = {}
            
            # Find courses this faculty can teach
            for course_id, faculty_list in self.course_faculty_map.items():
                if faculty_id in faculty_list:
                    self.assignment_vars[faculty_id][course_id] = {}
                    
                    for slot_id in all_slots:
                        # Only create for lecture slots
                        if 'L' in slot_id:
                            var_name = f"assign_{faculty_id}_{course_id}_{slot_id}"
                            self.assignment_vars[faculty_id][course_id][slot_id] = \
                                self.model.NewBoolVar(var_name)
        
        # Create slot used variables (for objective)
        for slot_id in all_slots:
            if 'L' in slot_id:
                self.slot_used_vars[slot_id] = self.model.NewBoolVar(f"used_{slot_id}")
        
        logger.info(f"Created variables for {len(self.faculties)} faculties, "
                   f"{len(self.courses)} courses, and {len(all_slots)} slots")
    
    def _add_constraints(self):
        """Add all constraints to the model"""
        
        # 1. Each slot can have at most one course
        self._add_slot_capacity_constraints()
        
        # 2. Each course must have exactly weekly_lectures sessions
        self._add_course_workload_constraints()
        
        # 3. Each faculty has max hours per week
        self._add_faculty_workload_constraints()
        
        # 4. Link slot_used variables to assignments
        self._add_slot_used_constraints()
        
        # 5. No overlapping for same section
        self._add_section_no_overlap_constraints()
        
        # 6. Faculty availability by day
        self._add_faculty_availability_constraints()
        
        # 7. Break constraints (from structure)
        self._add_break_constraints()
        
        # 8. Lab consecutive slot constraints
        self._add_lab_consecutive_constraints()
        
        logger.info("Added all constraints to model")
    
    def _add_slot_capacity_constraints(self):
        """Each slot can have at most one course assigned"""
        all_slots = []
        for day_slots in self.slot_ids.values():
            all_slots.extend(day_slots)
        
        for slot_id in all_slots:
            if 'L' not in slot_id:
                continue
                
            # Collect all variables that could assign to this slot
            slot_vars = []
            for faculty_id in self.assignment_vars:
                for course_id in self.assignment_vars[faculty_id]:
                    if slot_id in self.assignment_vars[faculty_id][course_id]:
                        slot_vars.append(self.assignment_vars[faculty_id][course_id][slot_id])
            
            if slot_vars:
                self.model.Add(sum(slot_vars) <= 1)
    
    def _add_course_workload_constraints(self):
        """Each course must have exactly weekly_lectures sessions"""
        for course_id, course in self.courses.items():
            weekly = course['weekly_lectures']
            
            # Collect all variables for this course
            course_vars = []
            for faculty_id in self.assignment_vars:
                if course_id in self.assignment_vars[faculty_id]:
                    course_vars.extend(self.assignment_vars[faculty_id][course_id].values())
            
            if course_vars:
                self.model.Add(sum(course_vars) == weekly)
                logger.info(f"Course {course_id} requires exactly {weekly} sessions")
    
    def _add_faculty_workload_constraints(self):
        """Each faculty has max hours per week"""
        for faculty_id, faculty in self.faculties.items():
            if faculty_id not in self.assignment_vars:
                continue
                
            # Collect all variables for this faculty
            faculty_vars = []
            for course_vars in self.assignment_vars[faculty_id].values():
                faculty_vars.extend(course_vars.values())
            
            if faculty_vars:
                self.model.Add(sum(faculty_vars) <= faculty['max_hours'])
                logger.info(f"Faculty {faculty_id} max {faculty['max_hours']} hours")
    
    def _add_slot_used_constraints(self):
        """Link slot_used variables to assignments"""
        for slot_id, used_var in self.slot_used_vars.items():
            # Collect all assignments for this slot
            slot_vars = []
            for faculty_id in self.assignment_vars:
                for course_id in self.assignment_vars[faculty_id]:
                    if slot_id in self.assignment_vars[faculty_id][course_id]:
                        slot_vars.append(self.assignment_vars[faculty_id][course_id][slot_id])
            
            if slot_vars:
                # used_var = 1 if any assignment is 1
                self.model.AddMaxEquality(used_var, slot_vars)
    
    def _add_section_no_overlap_constraints(self):
        """A section cannot have two courses at the same time"""
        # Group slots by time across days
        for section in self.sections:
            section_courses = self.section_courses_map.get(section, [])
            
            for day, slots in self.timetable_structure.items():
                for slot in slots:
                    if slot.get('type') != 'lecture':
                        continue
                    
                    slot_id = slot.get('slot_id')
                    if not slot_id:
                        continue
                    
                    # Collect all assignments for this section at this time
                    section_vars = []
                    for faculty_id in self.assignment_vars:
                        for course_id in section_courses:
                            if (course_id in self.assignment_vars[faculty_id] and 
                                slot_id in self.assignment_vars[faculty_id][course_id]):
                                section_vars.append(
                                    self.assignment_vars[faculty_id][course_id][slot_id]
                                )
                    
                    if section_vars:
                        self.model.Add(sum(section_vars) <= 1)
    
    def _add_faculty_availability_constraints(self):
        """Faculty can only teach on available days"""
        for faculty_id, faculty in self.faculties.items():
            available_days = faculty.get('available_days', [])
            
            for day, slots in self.timetable_structure.items():
                if day not in available_days:
                    # This faculty cannot teach on this day
                    for slot in slots:
                        slot_id = slot.get('slot_id')
                        if not slot_id or 'L' not in slot_id:
                            continue
                        
                        if faculty_id in self.assignment_vars:
                            for course_id in self.assignment_vars[faculty_id]:
                                if slot_id in self.assignment_vars[faculty_id][course_id]:
                                    self.model.Add(
                                        self.assignment_vars[faculty_id][course_id][slot_id] == 0
                                    )
    
    def _add_break_constraints(self):
        """Ensure break slots are never used"""
        for day, slots in self.timetable_structure.items():
            for slot in slots:
                if slot.get('type') == 'break':
                    slot_id = slot.get('slot_id')
                    if slot_id and slot_id in self.slot_used_vars:
                        self.model.Add(self.slot_used_vars[slot_id] == 0)
    
    def _add_lab_consecutive_constraints(self):
        """
        Ensure lab courses use consecutive slots
        If a lab is assigned to slot i, it must also be assigned to slot i+1
        """
        # Group slots by day
        slots_by_day = {}
        for day, slots in self.timetable_structure.items():
            day_slots = []
            for slot in slots:
                if slot.get('type') == 'lecture':
                    slot_id = slot.get('slot_id')
                    if slot_id:
                        day_slots.append(slot_id)
            # Sort by start time
            day_slots.sort()
            slots_by_day[day] = day_slots
        
        # Find lab courses
        for course_id, course in self.courses.items():
            if course.get('requires_lab', False) or course.get('weekly_labs', 0) > 0:
                # For each day, check consecutive slots
                for day, day_slots in slots_by_day.items():
                    for i in range(len(day_slots) - 1):
                        current_slot = day_slots[i]
                        next_slot = day_slots[i + 1]
                        
                        # Collect variables for this course in these slots
                        current_vars = []
                        next_vars = []
                        
                        for faculty_id in self.assignment_vars:
                            if course_id in self.assignment_vars[faculty_id]:
                                if current_slot in self.assignment_vars[faculty_id][course_id]:
                                    current_vars.append(
                                        self.assignment_vars[faculty_id][course_id][current_slot]
                                    )
                                if next_slot in self.assignment_vars[faculty_id][course_id]:
                                    next_vars.append(
                                        self.assignment_vars[faculty_id][course_id][next_slot]
                                    )
                        
                        # If this course is assigned to current slot, it must also be assigned to next slot
                        if current_vars and next_vars:
                            for current_var in current_vars:
                                for next_var in next_vars:
                                    # current_var => next_var
                                    self.model.AddImplication(current_var, next_var)
        
        logger.info("Added lab consecutive slot constraints")
    
    def _set_objective(self):
        """Maximize total assigned slots"""
        if self.slot_used_vars:
            self.model.Maximize(sum(self.slot_used_vars.values()))
            logger.info(f"Objective: maximize {len(self.slot_used_vars)} slots")
    
    def solve(self) -> Dict[str, Any]:
        """Solve the model and return results"""
        solver = cp_model.CpSolver()
        
        # Set time limit (optional)
        solver.parameters.max_time_in_seconds = 60
        
        status = solver.Solve(self.model)
        
        result = {
            'status': 'unknown',
            'assignments': {},
            'faculty_schedules': {},
            'course_schedules': {},
            'section_schedules': {}
        }
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            result['status'] = 'feasible'
            
            # Extract assignments
            for faculty_id in self.assignment_vars:
                result['faculty_schedules'][faculty_id] = []
                
                for course_id in self.assignment_vars[faculty_id]:
                    for slot_id, var in self.assignment_vars[faculty_id][course_id].items():
                        if solver.Value(var) == 1:
                            assignment = {
                                'faculty_id': faculty_id,
                                'faculty_name': self.faculties[faculty_id]['name'],
                                'course_id': course_id,
                                'course_code': self.courses[course_id]['code'],
                                'course_name': self.courses[course_id]['name'],
                                'section': self.courses[course_id]['section'],
                                'slot_id': slot_id
                            }
                            
                            # Store in various formats
                            result['assignments'][slot_id] = assignment
                            result['faculty_schedules'][faculty_id].append(assignment)
                            
                            # Group by course
                            if course_id not in result['course_schedules']:
                                result['course_schedules'][course_id] = []
                            result['course_schedules'][course_id].append(assignment)
                            
                            # Group by section
                            section = self.courses[course_id]['section']
                            if section not in result['section_schedules']:
                                result['section_schedules'][section] = []
                            result['section_schedules'][section].append(assignment)
            
            logger.info(f"Found feasible solution with {len(result['assignments'])} assignments")
        
        elif status == cp_model.INFEASIBLE:
            result['status'] = 'infeasible'
            logger.warning("Model is infeasible")
        
        return result
    
    def get_model(self) -> cp_model.CpModel:
        return self.model


# For backward compatibility
TimetableModel = EnhancedTimetableModel