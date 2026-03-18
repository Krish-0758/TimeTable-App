"""
Constraint translation layer for the CP-SAT solver.
"""

from typing import Dict, List
import logging

from ortools.sat.python import cp_model

from app.constraints.schema import (
    ConstraintBase,
    FacultyConstraint,
    SubjectConstraint,
    RoomConstraint,
    SpecialConstraint,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnsupportedConstraintError(Exception):
    """Raised when a constraint type is not supported by the solver."""


# =========================================================
# FACULTY CONSTRAINTS
# =========================================================

def apply_faculty_constraint(
    model: cp_model.CpModel,
    assignment_vars: Dict[str, cp_model.IntVar],
    constraint: FacultyConstraint,
    timetable_structure: Dict[str, List[dict]],
) -> None:
    """
    Translates a FacultyConstraint into solver constraints.
    """
    params = constraint.parameters
    faculty_id = params.get('faculty_id')
    faculty_name = params.get('faculty_name')
    
    logger.info(f"Applying faculty constraint for {faculty_id or faculty_name}")
    
    # For now, just log - will implement fully later
    pass


# =========================================================
# SUBJECT CONSTRAINTS
# =========================================================

def apply_max_lectures_per_day_constraint(
    model: cp_model.CpModel,
    assignment_vars: Dict[str, cp_model.IntVar],
    timetable_structure: Dict[str, List[dict]],
    constraint: SubjectConstraint,
) -> None:
    """
    Enforces: For each day, sum(assigned lecture slots) <= max_lectures_per_day
    """
    max_per_day = constraint.parameters.get("max_lectures_per_day")

    if max_per_day is None:
        logger.warning(f"SubjectConstraint {constraint.constraint_id} missing 'max_lectures_per_day'")
        return

    for day, slots in timetable_structure.items():
        lecture_vars = []

        for slot in slots:
            if slot.get("type") == "lecture":
                slot_id = slot.get("slot_id")
                if slot_id and slot_id in assignment_vars:
                    lecture_vars.append(assignment_vars[slot_id])

        if lecture_vars:
            model.Add(sum(lecture_vars) <= max_per_day)
            logger.info(f"Added max {max_per_day} lectures per day for {day}")


def apply_subject_constraint(
    model: cp_model.CpModel,
    assignment_vars: Dict[str, cp_model.IntVar],
    constraint: SubjectConstraint,
    timetable_structure: Dict[str, List[dict]],
) -> None:
    """
    Dispatches subject constraint semantics.
    """
    if "max_lectures_per_day" in constraint.parameters:
        apply_max_lectures_per_day_constraint(
            model,
            assignment_vars,
            timetable_structure,
            constraint,
        )
        return

    logger.info(f"Subject constraint {constraint.constraint_id} applied (basic)")


# =========================================================
# ROOM CONSTRAINTS
# =========================================================

def apply_room_constraint(
    model: cp_model.CpModel,
    assignment_vars: Dict[str, cp_model.IntVar],
    constraint: RoomConstraint,
    timetable_structure: Dict[str, List[dict]],
) -> None:
    """
    Translates a RoomConstraint into solver constraints.
    """
    params = constraint.parameters
    room_id = params.get('room_id') or params.get('room_number')
    
    logger.info(f"Applying room constraint for {room_id}")
    
    # Handle unavailable slots if specified
    unavailable_slots = params.get('unavailable_slots', [])
    if unavailable_slots:
        for slot_id, var in assignment_vars.items():
            for unavailable in unavailable_slots:
                if unavailable in slot_id:
                    model.Add(var == 0)
                    logger.info(f"Blocked unavailable slot {slot_id} for room {room_id}")


# =========================================================
# SPECIAL CONSTRAINTS (Industry Talk, Proctor Meeting, etc.)
# =========================================================

def apply_special_constraint(
    model: cp_model.CpModel,
    assignment_vars: Dict[str, cp_model.IntVar],
    constraint: ConstraintBase,
    timetable_structure: Dict[str, List[dict]],
) -> None:
    """
    Apply special constraints like Industry Talk, Proctor Meeting.
    These block specific time slots from having regular classes.
    """
    params = constraint.parameters
    constraint_type = params.get("type", "special")
    day = params.get("day")
    start_time = params.get("start_time")
    
    if not day or not start_time:
        logger.warning(f"Special constraint missing day/time: {constraint.constraint_id}")
        return
    
    # Find matching slots and block them
    blocked_count = 0
    for day_name, slots in timetable_structure.items():
        if day_name == day:
            for slot in slots:
                if slot.get("start_time") == start_time:
                    slot_id = slot.get("slot_id")
                    if slot_id and slot_id in assignment_vars:
                        # Force this slot to 0 (no class)
                        model.Add(assignment_vars[slot_id] == 0)
                        blocked_count += 1
                        logger.info(f"Blocked {day} {start_time} for {constraint_type}")
    
    if blocked_count == 0:
        logger.warning(f"No matching slot found for {day} {start_time}")


# =========================================================
# DISPATCHER
# =========================================================

def apply_constraint(
    model: cp_model.CpModel,
    assignment_vars: Dict[str, cp_model.IntVar],
    constraint: ConstraintBase,
    timetable_structure: Dict[str, List[dict]],
) -> None:
    """
    Dispatches a constraint object to the correct translation function.
    Checks by constraint_type first, then by isinstance.
    """
    try:
        # First check by constraint_type string (most reliable)
        if constraint.constraint_type == "faculty":
            apply_faculty_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        elif constraint.constraint_type == "subject":
            apply_subject_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        elif constraint.constraint_type == "room":
            apply_room_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        elif constraint.constraint_type == "special":
            apply_special_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        # Fall back to isinstance checks for backward compatibility
        elif isinstance(constraint, FacultyConstraint):
            apply_faculty_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        elif isinstance(constraint, SubjectConstraint):
            apply_subject_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        elif isinstance(constraint, RoomConstraint):
            apply_room_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        elif isinstance(constraint, SpecialConstraint):
            apply_special_constraint(
                model,
                assignment_vars,
                constraint,
                timetable_structure,
            )
        else:
            raise UnsupportedConstraintError(
                f"Unsupported constraint type: {constraint.constraint_type}"
            )
    except Exception as e:
        logger.error(f"Error applying constraint {constraint.constraint_id}: {e}")
        raise