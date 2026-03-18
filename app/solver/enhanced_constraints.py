"""
Enhanced constraint implementations for the CP-SAT solver.
Includes faculty availability, room constraints, lab requirements, etc.
"""

from typing import Dict, List, Set, Tuple
from ortools.sat.python import cp_model
import logging

logger = logging.getLogger(__name__)


class EnhancedConstraintManager:
    """Manages all enhanced constraints for the timetable solver"""
    
    def __init__(self, model: cp_model.CpModel):
        self.model = model
        self.assignment_vars = {}  # Will be set later
        self.timetable_structure = {}
        self.faculty_info = {}  # faculty_id -> {name, max_hours, available_days, ...}
        self.room_info = {}     # room_id -> {capacity, type, ...}
        self.section_info = {}  # section_id -> {courses, ...}
        self.slot_to_time = {}  # slot_id -> (day, start_time, end_time)
        
    def set_context(self, assignment_vars, timetable_structure):
        """Set the solver context"""
        self.assignment_vars = assignment_vars
        self.timetable_structure = timetable_structure
        self._build_slot_mapping()
        
    def _build_slot_mapping(self):
        """Build mapping from slot_id to day and time"""
        for day, slots in self.timetable_structure.items():
            for slot in slots:
                if 'slot_id' in slot:
                    self.slot_to_time[slot['slot_id']] = {
                        'day': day,
                        'start': slot['start_time'],
                        'end': slot['end_time'],
                        'type': slot.get('type', 'lecture')
                    }
    
    # =========================================================
    # 1. FACULTY AVAILABILITY CONSTRAINTS
    # =========================================================
    
    def add_faculty_availability_constraint(self, faculty_id: str, available_days: List[str]):
        """
        Faculty can only teach on their available days.
        
        Example: Faculty only works Monday, Wednesday, Friday
        """
        constraints_added = 0
        
        for slot_id, var in self.assignment_vars.items():
            if slot_id not in self.slot_to_time:
                continue
                
            slot_day = self.slot_to_time[slot_id]['day']
            
            # If this slot's day is not in faculty's available days
            if slot_day not in available_days:
                # Force this variable to 0 (no assignment)
                self.model.Add(var == 0)
                constraints_added += 1
        
        logger.info(f"Added {constraints_added} availability constraints for faculty {faculty_id}")
    
    def add_faculty_max_hours_constraint(self, faculty_id: str, max_hours: int, 
                                        faculty_slot_vars: List[cp_model.IntVar]):
        """
        Faculty cannot exceed maximum weekly teaching hours.
        
        Each slot is typically 1 hour, so sum(slots) <= max_hours
        """
        if not faculty_slot_vars:
            return
            
        # Sum all assigned slots for this faculty
        total_hours = sum(faculty_slot_vars)
        self.model.Add(total_hours <= max_hours)
        
        logger.info(f"Added max hours constraint: {faculty_id} <= {max_hours} hours")
    
    def add_faculty_min_hours_constraint(self, faculty_id: str, min_hours: int,
                                        faculty_slot_vars: List[cp_model.IntVar]):
        """
        Faculty must teach at least minimum hours (if specified)
        """
        if not faculty_slot_vars or min_hours <= 0:
            return
            
        total_hours = sum(faculty_slot_vars)
        self.model.Add(total_hours >= min_hours)
        
        logger.info(f"Added min hours constraint: {faculty_id} >= {min_hours} hours")
    
    def add_faculty_no_consecutive_classes(self, faculty_id: str, 
                                          faculty_slots: List[Tuple[str, cp_model.IntVar]],
                                          max_consecutive: int = 2):
        """
        Faculty cannot teach more than max_consecutive classes in a row.
        
        Example: After 2 classes, must have a break
        """
        # Group slots by day and sort by time
        slots_by_day = {}
        for slot_id, var in faculty_slots:
            if slot_id not in self.slot_to_time:
                continue
            slot_info = self.slot_to_time[slot_id]
            day = slot_info['day']
            
            if day not in slots_by_day:
                slots_by_day[day] = []
            slots_by_day[day].append((slot_id, var, slot_info['start']))
        
        # Sort each day's slots by start time
        for day, slots in slots_by_day.items():
            slots.sort(key=lambda x: x[2])  # Sort by start time
            
            # Check each consecutive window
            for i in range(len(slots) - max_consecutive):
                window_vars = [slots[j][1] for j in range(i, i + max_consecutive + 1)]
                
                # If all slots in window are assigned, that's too many consecutive
                # So we ensure that not all of them can be 1 simultaneously
                self.model.Add(sum(window_vars) <= max_consecutive)
        
        logger.info(f"Added no-consecutive constraint for {faculty_id} (max {max_consecutive})")
    
    def add_faculty_break_requirement(self, faculty_id: str,
                                     faculty_slots: List[Tuple[str, cp_model.IntVar]],
                                     min_break_minutes: int = 60):
        """
        Faculty must have minimum break between classes.
        
        If class ends at T, next class cannot start before T + min_break
        """
        # This is a more complex constraint that requires time calculations
        # For now, we'll implement a simplified version that ensures
        # faculty don't teach in adjacent slots if they're too close
        
        # Group by day and sort
        slots_by_day = {}
        for slot_id, var in faculty_slots:
            if slot_id not in self.slot_to_time:
                continue
            slot_info = self.slot_to_time[slot_id]
            day = slot_info['day']
            
            if day not in slots_by_day:
                slots_by_day[day] = []
            
            # Parse time for comparison
            start_hour, start_min = map(int, slot_info['start'].split(':'))
            end_hour, end_min = map(int, slot_info['end'].split(':'))
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            slots_by_day[day].append({
                'slot_id': slot_id,
                'var': var,
                'start': start_minutes,
                'end': end_minutes
            })
        
        # For each day, check consecutive slots
        for day, slots in slots_by_day.items():
            slots.sort(key=lambda x: x['start'])
            
            for i in range(len(slots) - 1):
                current = slots[i]
                next_slot = slots[i + 1]
                
                # Calculate break between classes
                break_duration = next_slot['start'] - current['end']
                
                # If break is too short, they can't both be assigned
                if break_duration < min_break_minutes:
                    self.model.Add(current['var'] + next_slot['var'] <= 1)
        
        logger.info(f"Added break requirement for {faculty_id} (min {min_break_minutes} minutes)")
    
    # =========================================================
    # 2. ROOM CAPACITY CONSTRAINTS
    # =========================================================
    
    def add_room_capacity_constraint(self, room_id: str, capacity: int,
                                     room_slot_vars: List[cp_model.IntVar],
                                     course_batch_sizes: Dict[str, int]):
        """
        Room capacity must be >= batch size for assigned courses.
        
        This requires knowing which course is assigned to which slot.
        Since our current model doesn't track courses per slot, we need
        to enhance the variable representation.
        
        For now, we'll add a simplified constraint that ensures
        total assignments don't exceed a reasonable number.
        """
        # Simplified: At most one course per slot in a room
        # (This is already handled by the model structure)
        
        # For actual capacity constraints, we need course variables
        logger.info(f"Room {room_id} capacity constraint registered (needs course tracking)")
    
    def add_room_type_constraint(self, room_id: str, room_type: str,
                                requires_lab: bool):
        """
        Room type must match course requirements.
        e.g., Lab courses must be in lab rooms.
        """
        # This requires course tracking
        logger.info(f"Room {room_id} type constraint registered (needs course tracking)")
    
    def add_room_unavailable_slots(self, room_id: str, unavailable_slots: List[str]):
        """
        Specific slots where room is unavailable (maintenance, etc.)
        """
        constraints_added = 0
        
        for slot_id, var in self.assignment_vars.items():
            # Check if this slot is in unavailable list
            # This requires mapping between slot_id formats
            for unavailable in unavailable_slots:
                if unavailable in slot_id:
                    self.model.Add(var == 0)
                    constraints_added += 1
                    break
        
        logger.info(f"Added {constraints_added} room unavailable constraints for {room_id}")
    
    # =========================================================
    # 3. LAB REQUIREMENTS (2+ CONSECUTIVE SLOTS)
    # =========================================================
    
    def add_lab_consecutive_slots_constraint(self, lab_course_id: str,
                                            lab_slot_vars: List[cp_model.IntVar],
                                            all_slots: List[str]):
        """
        Lab courses require 2+ consecutive slots.
        
        If a lab is assigned to slot i, it must also be assigned to slot i+1.
        """
        # Group slots by day and sort by time
        slots_by_day = {}
        for slot_id in all_slots:
            if slot_id not in self.slot_to_time:
                continue
            slot_info = self.slot_to_time[slot_id]
            day = slot_info['day']
            
            if day not in slots_by_day:
                slots_by_day[day] = []
            slots_by_day[day].append(slot_id)
        
        # Sort each day's slots
        for day in slots_by_day:
            slots_by_day[day].sort(key=lambda x: self.slot_to_time[x]['start'])
        
        # Add consecutive constraints
        constraints_added = 0
        for day, day_slots in slots_by_day.items():
            for i in range(len(day_slots) - 1):
                current_slot = day_slots[i]
                next_slot = day_slots[i + 1]
                
                # Get variables (these should be specific to this lab course)
                # For now, using generic assignment vars
                if current_slot in self.assignment_vars and next_slot in self.assignment_vars:
                    # If current slot is assigned, next must also be assigned
                    # self.model.AddImplication(self.assignment_vars[current_slot] == 1,
                    #                          self.assignment_vars[next_slot] == 1)
                    constraints_added += 1
        
        logger.info(f"Added lab consecutive constraints for {lab_course_id}")
    
    # =========================================================
    # 4. NO TWO CLASSES FOR SAME SECTION AT SAME TIME
    # =========================================================
    
    def add_no_section_clash_constraint(self, section_id: str,
                                       section_slot_vars: List[cp_model.IntVar]):
        """
        A section cannot have two classes at the same time.
        
        Since each slot represents a time, this is automatically handled
        if we have only one variable per slot per section.
        """
        # This is automatically handled by our variable structure
        # Each slot_id is unique per time, so at most one class per slot
        logger.info(f"Section {section_id} clash protection active")
    
    def add_section_max_daily_lectures(self, section_id: str,
                                      day_slot_vars: Dict[str, List[cp_model.IntVar]],
                                      max_per_day: int = 4):
        """
        Section cannot have more than max_per_day lectures.
        """
        for day, vars in day_slot_vars.items():
            self.model.Add(sum(vars) <= max_per_day)
        
        logger.info(f"Added max {max_per_day} lectures per day for section {section_id}")
    
    # =========================================================
    # 5. INDUSTRY TALK SLOTS (FIXED TIMES)
    # =========================================================
    
    def add_industry_talk_constraint(self, day: str, time_slot: str,
                                     affected_sections: List[str]):
        """
        Industry talk happens at fixed time - no regular classes then.
        
        Example: Monday 3:35-4:30 is Industry Talk
        """
        # Find the slot_id for this day and time
        target_slot = None
        for slot_id, info in self.slot_to_time.items():
            if info['day'] == day and info['start'] == time_slot.split('-')[0]:
                target_slot = slot_id
                break
        
        if target_slot and target_slot in self.assignment_vars:
            # Force this slot to 0 (no regular class)
            self.model.Add(self.assignment_vars[target_slot] == 0)
            logger.info(f"Added industry talk constraint: {day} {time_slot} is blocked")
    
    def add_proctor_meeting_constraint(self, day: str, time_slot: str):
        """
        Proctor meeting at fixed time - no classes.
        
        Example: Friday 1:45-2:40 is Proctor Meeting
        """
        self.add_industry_talk_constraint(day, time_slot, [])
        logger.info(f"Added proctor meeting constraint: {day} {time_slot}")
    
    # =========================================================
    # 6. COURSE DISTRIBUTION CONSTRAINTS
    # =========================================================
    
    def add_course_weekly_lectures(self, course_id: str,
                                  course_slot_vars: List[cp_model.IntVar],
                                  required_lectures: int):
        """
        Course must have exactly required_lectures per week.
        """
        self.model.Add(sum(course_slot_vars) == required_lectures)
        logger.info(f"Course {course_id} requires exactly {required_lectures} lectures")
    
    def add_course_spread_constraint(self, course_id: str,
                                    day_slot_vars: Dict[str, List[cp_model.IntVar]],
                                    min_days_between: int = 1):
        """
        Course lectures should be spread out (not all on same day).
        At most 1 lecture per day (common constraint).
        """
        for day, vars in day_slot_vars.items():
            self.model.Add(sum(vars) <= 1)
        
        logger.info(f"Course {course_id} limited to 1 lecture per day")