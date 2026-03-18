from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException

from app.core.structure import TimetableStructure
from app.core.slots import generate_slot_id
from app.constraints.schema import (
    ConstraintBase,
    FacultyConstraint,
    SubjectConstraint,
    RoomConstraint,
)
from app.constraints.validator import validate_constraints
from app.solver.model import TimetableModel
from app.solver.solve import solve_timetable
router = APIRouter()

# -----------------------------
# In-memory stores (backend-only)
# -----------------------------

TIMETABLE_STRUCTURE: Optional[Dict[str, List[Dict[str, Any]]]] = None
SLOT_IDS: Optional[Dict[str, List[str]]] = None
CONSTRAINTS: List[ConstraintBase] = []


# -----------------------------
# Create timetable structure
# -----------------------------

@router.post("/structure")
def create_structure(payload: Dict[str, Any]):
    """
    Creates and stores the timetable structure and slot IDs.
    """
    global TIMETABLE_STRUCTURE, SLOT_IDS, CONSTRAINTS

    try:
        structure = TimetableStructure(
            working_days=payload["working_days"],
            day_start_time=payload["day_start_time"],
            day_end_time=payload["day_end_time"],
            lecture_duration_minutes=payload["lecture_duration_minutes"],
            breaks=payload.get("breaks", []),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required field: {exc}",
        )

    week_structure = structure.generate()

    slot_ids: Dict[str, List[str]] = {}

    for day, slots in week_structure.items():
        slot_ids[day] = []
        for slot in slots:
            slot_id = generate_slot_id(
                day=day,
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                slot_type=slot["type"],
            )
            slot["slot_id"] = slot_id
            slot_ids[day].append(slot_id)

    # Reset state on new structure
    TIMETABLE_STRUCTURE = week_structure
    SLOT_IDS = slot_ids
    CONSTRAINTS.clear()

    return {
        "status": "structure_created",
        "days": list(week_structure.keys()),
        "slot_count": sum(len(slots) for slots in slot_ids.values())
    }


# -----------------------------
# Add constraint (manual JSON input)
# -----------------------------

@router.post("/constraints")
def add_constraint(payload: Dict[str, Any]):
    """
    Adds a validated constraint to the system.
    Expected format:
    {
        "constraint_id": "string",
        "constraint_type": "faculty" | "subject" | "room",
        "hardness": "hard" | "soft",
        "parameters": { ... }
    }
    """
    try:
        constraint_type = payload.get("constraint_type")

        if constraint_type == "faculty":
            constraint = FacultyConstraint(**payload)
        elif constraint_type == "subject":
            constraint = SubjectConstraint(**payload)
        elif constraint_type == "room":
            constraint = RoomConstraint(**payload)
        else:
            raise ValueError("Invalid or missing constraint_type")

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    CONSTRAINTS.append(constraint)

    return {
        "status": "constraint_added",
        "constraint_id": constraint.constraint_id,
        "total_constraints": len(CONSTRAINTS)
    }


# -----------------------------
# Add multiple constraints at once
# -----------------------------

@router.post("/constraints/batch")
def add_constraints_batch(payload: List[Dict[str, Any]]):
    """
    Adds multiple validated constraints at once.
    """
    added_ids = []
    errors = []

    for idx, constraint_data in enumerate(payload):
        try:
            constraint_type = constraint_data.get("constraint_type")

            if constraint_type == "faculty":
                constraint = FacultyConstraint(**constraint_data)
            elif constraint_type == "subject":
                constraint = SubjectConstraint(**constraint_data)
            elif constraint_type == "room":
                constraint = RoomConstraint(**constraint_data)
            elif constraint_type == "special":
                constraint = SpecialConstraint(**constraint_data)  # Make sure this line exists
            else:
                raise ValueError(f"Invalid constraint_type at index {idx}")

            CONSTRAINTS.append(constraint)
            added_ids.append(constraint.constraint_id)

        except Exception as exc:
            errors.append(f"Item {idx}: {str(exc)}")

    return {
        "status": "batch_processed",
        "added": len(added_ids),
        "failed": len(errors),
        "constraint_ids": added_ids,
        "errors": errors if errors else None
    }
    
# -----------------------------
# Validate constraints
# -----------------------------

@router.post("/constraints/validate")
def validate_all_constraints():
    """
    Validates all stored constraints.
    """
    try:
        validate_constraints(CONSTRAINTS)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "status": "constraints_valid",
        "count": len(CONSTRAINTS),
    }


# -----------------------------
# Get all constraints
# -----------------------------

@router.get("/constraints")
def get_all_constraints():
    """
    Returns all stored constraints.
    """
    return {
        "count": len(CONSTRAINTS),
        "constraints": [c.model_dump() for c in CONSTRAINTS]
    }


# -----------------------------
# Clear all constraints
# -----------------------------

@router.delete("/constraints")
def clear_constraints():
    """
    Clears all stored constraints.
    """
    global CONSTRAINTS
    CONSTRAINTS.clear()
    return {"status": "constraints_cleared"}


# -----------------------------
# Solve timetable
# -----------------------------

@router.post("/solve")
def solve():
    """
    Executes the enhanced timetable solver with current structure and constraints.
    """
    global TIMETABLE_STRUCTURE, SLOT_IDS, CONSTRAINTS
    
    if TIMETABLE_STRUCTURE is None or SLOT_IDS is None:
        raise HTTPException(
            status_code=400,
            detail="Timetable structure not created. Call POST /structure first.",
        )

    if not CONSTRAINTS:
        raise HTTPException(
            status_code=400,
            detail="No constraints added. Add constraints via POST /constraints first.",
        )

    # Use the enhanced model
    from app.solver.model import TimetableModel
    
    model = TimetableModel(
        timetable_structure=TIMETABLE_STRUCTURE,
        slot_ids=SLOT_IDS,
        constraints=CONSTRAINTS,
    )

    result = model.solve()
    return result
# -----------------------------
# Get current state
# -----------------------------

@router.get("/status")
def get_status():
    """
    Returns current system state.
    """
    return {
        "structure_created": TIMETABLE_STRUCTURE is not None,
        "days": list(TIMETABLE_STRUCTURE.keys()) if TIMETABLE_STRUCTURE else [],
        "total_slots": sum(len(slots) for slots in SLOT_IDS.values()) if SLOT_IDS else 0,
        "constraint_count": len(CONSTRAINTS),
        "hard_constraints": sum(1 for c in CONSTRAINTS if c.hardness == "hard"),
        "soft_constraints": sum(1 for c in CONSTRAINTS if c.hardness == "soft"),
    }


# -----------------------------
# Reset everything
# -----------------------------

@router.post("/reset")
def reset_system():
    """
    Resets the entire system state.
    """
    global TIMETABLE_STRUCTURE, SLOT_IDS, CONSTRAINTS
    TIMETABLE_STRUCTURE = None
    SLOT_IDS = None
    CONSTRAINTS.clear()
    return {"status": "system_reset"}