"""
Constraint definitions and validation for the Timetable Generator.
"""
from app.constraints.schema import (
    ConstraintBase,
    FacultyConstraint,
    SubjectConstraint,
    RoomConstraint,
)
from app.constraints.validator import validate_constraints