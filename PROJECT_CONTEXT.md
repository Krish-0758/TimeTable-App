# PROJECT_CONTEXT.md — Timetable Generator System

> **Purpose**: This document is intended to be fed to AI agents, code assistants, or any external system that needs a full understanding of this codebase. It covers architecture, all modules, the solver, constraints, the API, data formats, scripts, and operational workflows.

---

## 1. High-Level Overview

**Project Name**: Timetable Generator (v2.0.0)

**Goal**: Automatically generate collision-free weekly academic timetables for a college/university, satisfying hard constraints (faculty availability, room bookings, special events) and soft goals (maximize slot utilization). The system ingests real-world Excel data on subjects and faculty, converts it to a structured constraint format, and solves the scheduling problem using Google OR-Tools CP-SAT (Constraint Programming — Boolean Satisfiability).

**Technology Stack**:
| Layer | Technology |
|---|---|
| Language | Python 3.x |
| HTTP API | FastAPI + Uvicorn |
| Solver | Google OR-Tools `cp_model` (CP-SAT) |
| Data Validation | Pydantic v2 |
| Data Source | Excel `.xlsx` (via openpyxl/pandas in scripts) |
| Output | JSON, HTML timetable views |

**Repository Root**: `c:\Users\Krish Raj\Timetable\`

---

## 2. Directory Structure

```
Timetable/
│
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── run_real_data.py        # Orchestration script (extract → server → load)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # All REST API endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── constants.py        # Global constants (mostly placeholder)
│   │   ├── slots.py            # Slot ID generation utilities
│   │   └── structure.py        # TimetableStructure: time-slot grid generator
│   │
│   ├── constraints/
│   │   ├── __init__.py
│   │   ├── schema.py           # Pydantic constraint models (ConstraintBase + subtypes)
│   │   ├── store.py            # (Placeholder) constraint store
│   │   └── validator.py        # Basic constraint list validation
│   │
│   └── solver/
│       ├── __init__.py
│       ├── solve.py            # SolveResult wrapper + solve_timetable() entrypoint
│       ├── model.py            # EnhancedTimetableModel: CP-SAT model builder
│       ├── constraints.py      # Constraint-to-CP-SAT translation dispatcher
│       └── enhanced_constraints.py  # EnhancedConstraintManager: detailed constraint types
│
├── data/
│   ├── structure.json          # Default timetable time-grid config
│   ├── structure_with_specials.json  # Config with special slots blocked
│   ├── constraints.json        # (Placeholder for declarative constraints)
│   └── real/                   # Extracted real-world data (from Excel)
│       ├── faculty_constraints.json  # Per-faculty constraints (~38 entries)
│       ├── course_constraints.json   # Per-subject constraints (~25 entries)
│       ├── room_constraints.json     # Room constraints (~16 entries)
│       ├── special_constraints.json  # Special events (Industry Talk, Proctor Meeting)
│       ├── all_constraints_fixed.json # Merged complete constraint set
│       ├── complete_constraints.json  # Complete + validated
│       ├── working_constraints.json   # Working subset used by solver
│       └── summary.json              # Stats: {faculties:38, courses:25, assignments:99, rooms:16, total_constraints:81}
│
├── scripts/                    # Utility and data pipeline scripts
│   ├── client.py               # HTTP client to drive the API (workflow helper)
│   ├── data_extractor.py       # Core Excel → JSON extractor
│   ├── extract_real_constraints.py  # Full extraction pipeline from Excel
│   ├── extract_master_timetable.py  # Extracts master timetable from output
│   ├── load_real_data.py       # Loads extracted data into running API
│   ├── generate_structure.py   # Generates structure JSON
│   ├── format_timetable.py     # Formats raw timetable output to display format
│   ├── simple_timetable_viewer.py   # Simple HTML timetable renderer
│   ├── visual_timetable.py     # Full featured HTML/visual timetable renderer
│   ├── visual_timetable_real.py     # Visual renderer using real data
│   ├── visual_with_names.py    # Visual renderer with faculty names
│   ├── section_wise_timetable.py    # Per-section timetable views
│   ├── import_timetable_data.py     # Imports timetable data
│   ├── add_specials_to_structure.py # Adds special slots to structure JSON
│   ├── check_specials.py       # Validates special constraints
│   ├── fix_special_constraints.py   # Patches special constraint format issues
│   ├── analyze_assignments.py  # Post-solve analysis
│   ├── debug_indices.py        # Debug helper for index issues
│   ├── show_enhanced_timetable.py  # Enhanced display
│   ├── view_timetable.py       # Timetable viewer
│   ├── simple_visual.py        # Simplified visual output
│   └── packed.py               # All-in-one packed script version
│
├── docs/
│   ├── api.md                  # (Placeholder — empty)
│   └── examples.md             # (Placeholder — empty)
│
├── examples/
│   └── room_constraint.json    # Example room constraint JSON
│
├── tests/                      # Test directory (pytest)
│
├── run.py                      # CLI convenience launcher
├── AY 2025_2026 ODD SUBJECT ALLOTMENT_JULY 2025.xlsx   # Source Excel data
├── timetable_solution.json     # Sample solver output
└── *.html                      # Generated HTML timetable views
```

---

## 3. Core Concepts

### 3.1 Timetable Structure (Time Grid)

The "structure" defines the temporal skeleton of the timetable — the working days, what time classes start/end, lecture slot duration, and where breaks fall. It is completely content-free (no subjects, no faculty).

**Config fields** (`data/structure.json`):
```json
{
  "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  "day_start_time": "09:00",
  "day_end_time": "16:30",
  "lecture_duration_minutes": 55,
  "breaks": [
    {"label": "Morning Break", "start_time": "10:50", "end_time": "11:05"},
    {"label": "Lunch",         "start_time": "12:50", "end_time": "13:45"}
  ]
}
```

**With special slots** (`data/structure_with_specials.json`): adds two more "breaks":
- `Industry Talk` — Monday 15:35–16:30
- `Proctor Meeting` — Friday 13:45–14:40

**Output**: A dictionary mapping `day → list of slots`, where each slot is either:
```json
{"type": "lecture", "start_time": "09:00", "end_time": "09:55", "slot_id": "MON_0900_0955_L"}
{"type": "break",   "label": "Lunch",     "start_time": "12:50", "end_time": "13:45", "slot_id": "MON_1250_1345_B"}
```

### 3.2 Slot IDs

**Module**: `app/core/slots.py` → `generate_slot_id()`

Slot IDs are deterministic, stable, and unique strings:

```
Format: {DAY_CODE}_{START_HHMM}_{END_HHMM}_{TYPE_CODE}
Example: MON_0900_0955_L   (Monday lecture 09:00–09:55)
         FRI_1250_1345_B   (Friday break 12:50–13:45)
```

- `DAY_CODE` = first 3 upper-case letters of the day name
- `TYPE_CODE` = `L` for lecture, `B` for break
- Only lecture slots (`L`) are used as solver decision variable indices.
- Break slots are generated but never assigned to courses.

### 3.3 Constraints

Constraints are the primary mechanism to encode scheduling rules. They are Pydantic models validated at the API layer.

**Base model** (`app/constraints/schema.py`):
```python
class ConstraintBase(BaseModel):
    constraint_id: str       # Unique ID string (required, min length 1)
    constraint_type: Literal["faculty", "subject", "room", "special"]
    hardness: Literal["hard", "soft"]
    parameters: Dict[str, Any]  # Type-specific payload
```

**Subtypes**:
| Class | `constraint_type` | Purpose |
|---|---|---|
| `FacultyConstraint` | `"faculty"` | Encodes a faculty member's info and availability |
| `SubjectConstraint` | `"subject"` | Encodes a course/subject and its scheduling requirements |
| `RoomConstraint` | `"room"` | Encodes room info and unavailable slots |
| `SpecialConstraint` | `"special"` | Blocks fixed institutional slots (Industry Talk, Proctor Meeting) |

**Important**: Models are **immutable** (`frozen=True`) and **strict** (`extra="forbid"`). No extra parameters are allowed.

---

## 4. Constraint Parameter Schemas

### 4.1 Faculty Constraint
```json
{
  "constraint_id": "FAC_001",
  "constraint_type": "faculty",
  "hardness": "hard",
  "parameters": {
    "faculty_id": "F001",
    "faculty_name": "Dr. Smith",
    "max_hours_per_week": 20,
    "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
  }
}
```

### 4.2 Subject Constraint
```json
{
  "constraint_id": "SUB_CS101",
  "constraint_type": "subject",
  "hardness": "hard",
  "parameters": {
    "course_id": "CS101",
    "course_code": "CS101",
    "course_name": "Data Structures",
    "section": "A",
    "type": "theory",
    "weekly_lectures": 3,
    "faculty_ids": ["F001", "F002"],
    "max_lectures_per_day": 1
  }
}
```
- `type` can be `"theory"` or `"lab"`.
- `weekly_lectures` controls how many slots the solver must assign for this course per week.
- `faculty_ids` is the list of faculties who can teach this course.
- `max_lectures_per_day` is an optional sub-constraint applied by the dispatcher.

### 4.3 Room Constraint
```json
{
  "constraint_id": "ROOM_101",
  "constraint_type": "room",
  "hardness": "hard",
  "parameters": {
    "room_id": "101",
    "room_number": "101",
    "capacity": 60,
    "type": "classroom",
    "unavailable_slots": ["MON_0900_0955"]
  }
}
```

### 4.4 Special Constraint
```json
{
  "constraint_id": "SPECIAL_INDUSTRY_TALK_MON",
  "constraint_type": "special",
  "hardness": "hard",
  "parameters": {
    "type": "industry_talk",
    "day": "Monday",
    "start_time": "15:35",
    "end_time": "16:30",
    "description": "Industry Talk / Training"
  }
}
```

---

## 5. The CP-SAT Solver

### 5.1 Architecture

**Primary file**: `app/solver/model.py`

The solver is built around `EnhancedTimetableModel` (aliased as `TimetableModel`), which wraps Google OR-Tools `cp_model.CpModel`.

**Solver entry point** (`app/solver/solve.py`):
```python
result = solve_timetable(model_wrapper: TimetableModel) -> SolveResult
```

### 5.2 Decision Variables

The model creates **Boolean decision variables** of the form:

```
assignment[faculty_id][course_id][slot_id] ∈ {0, 1}
```

Meaning: "Does faculty `faculty_id` teach course `course_id` in slot `slot_id`?"

- Only lecture slots (`L` in slot_id) get variables.
- Variables are only created for (faculty, course) pairs where that faculty appears in `course.faculty_ids`.
- An additional `slot_used[slot_id] ∈ {0,1}` variable tracks whether any course is assigned to a slot (used for the objective function).

### 5.3 Hard Constraints Built Into the Model

| # | Constraint | Implementation |
|---|---|---|
| 1 | **Slot capacity** | Each slot can have at most 1 assignment: `sum(slot_vars) <= 1` |
| 2 | **Course workload** | Each course must have exactly `weekly_lectures` sessions: `sum(course_vars) == weekly_lectures` |
| 3 | **Faculty max hours** | Total assignments for a faculty `<= max_hours`: `sum(faculty_vars) <= max_hours` |
| 4 | **Slot-used linkage** | `used_var = max(slot_vars)` so slot_used accurately reflects whether the slot is occupied |
| 5 | **Section no-overlap** | Within the same section, at most one course per slot: `sum(section_slot_vars) <= 1` |
| 6 | **Faculty availability** | If a faculty is not available on a day, all variables in those day-slots are forced to 0 |
| 7 | **Break protection** | Variables for break slots (if any accidentally exist) are forced to 0 |

### 5.4 Objective Function

```python
model.Maximize(sum(slot_used_vars.values()))
```

The solver maximizes total number of filled lecture slots → it tries to schedule as many classes as possible within the given constraints.

### 5.5 Solver Parameters

```python
solver.parameters.max_time_in_seconds = 60  # 60-second time limit
```

The solver accepts `OPTIMAL` or `FEASIBLE` statuses. If `INFEASIBLE`, the model returns `status: "infeasible"`.

### 5.6 Solver Output Format

On success (`status: "feasible"`):
```json
{
  "status": "feasible",
  "assignments": {
    "MON_0900_0955_L": {
      "faculty_id": "F001",
      "faculty_name": "Dr. Smith",
      "course_id": "CS101",
      "course_code": "CS101",
      "course_name": "Data Structures",
      "section": "A",
      "slot_id": "MON_0900_0955_L"
    }
  },
  "faculty_schedules": {
    "F001": [ /* list of assignment objects */ ]
  },
  "course_schedules": {
    "CS101": [ /* list of assignment objects */ ]
  },
  "section_schedules": {
    "A": [ /* list of assignment objects */ ]
  }
}
```

---

## 6. Constraint Dispatcher (`app/solver/constraints.py`)

This module translates each `ConstraintBase` object into actual OR-Tools model additions. It is a **dispatcher** (not called by the model directly — in `model.py` the constraints are read for data extraction, while this module handles the low-level translation for the simpler original flow).

```
apply_constraint(model, assignment_vars, constraint, timetable_structure)
    │
    ├── constraint_type == "faculty"  → apply_faculty_constraint()
    ├── constraint_type == "subject"  → apply_subject_constraint()
    │       └── if "max_lectures_per_day" in params → apply_max_lectures_per_day_constraint()
    ├── constraint_type == "room"     → apply_room_constraint()
    │       └── blocks unavailable_slots
    └── constraint_type == "special" → apply_special_constraint()
            └── blocks the day+start_time slot by forcing var == 0
```

---

## 7. Enhanced Constraint Manager (`app/solver/enhanced_constraints.py`)

`EnhancedConstraintManager` provides a richer, object-oriented API for adding fine-grained constraints to the CP-SAT model. Used in more advanced scenarios.

| Method | Purpose |
|---|---|
| `add_faculty_availability_constraint(faculty_id, available_days)` | Block slots on unavailable days |
| `add_faculty_max_hours_constraint(faculty_id, max_hours, vars)` | `sum(vars) <= max_hours` |
| `add_faculty_min_hours_constraint(faculty_id, min_hours, vars)` | `sum(vars) >= min_hours` |
| `add_faculty_no_consecutive_classes(faculty_id, slots, max_consecutive)` | Sliding window: `sum(window_vars) <= max_consecutive` |
| `add_faculty_break_requirement(faculty_id, slots, min_break_minutes)` | For adjacent slots with gap < threshold: `var_a + var_b <= 1` |
| `add_room_unavailable_slots(room_id, unavailable_slots)` | Block specific room slots |
| `add_lab_consecutive_slots_constraint(lab_course_id, vars, all_slots)` | (Registered, partial impl) Lab requires 2+ consecutive slots |
| `add_no_section_clash_constraint(section_id, vars)` | (Auto-handled by variable structure) |
| `add_section_max_daily_lectures(section_id, day_vars, max_per_day)` | `sum(day_vars) <= max_per_day` |
| `add_industry_talk_constraint(day, time_slot, sections)` | Block slot at fixed time: `var == 0` |
| `add_proctor_meeting_constraint(day, time_slot)` | Block slot at fixed time: `var == 0` |
| `add_course_weekly_lectures(course_id, vars, required)` | `sum(vars) == required` |
| `add_course_spread_constraint(course_id, day_vars, min_days_between)` | `sum(day_vars) <= 1` per day |

---

## 8. REST API Reference

**Framework**: FastAPI  
**Entry**: `app/main.py` → `uvicorn app.main:app`  
**Base URL**: `http://localhost:8000`  
**Auto Docs**: `http://localhost:8000/docs`

### State (In-Memory, per server session)

| Variable | Type | Description |
|---|---|---|
| `TIMETABLE_STRUCTURE` | `Dict[str, List[Dict]]` | The active time-slot grid (per day) |
| `SLOT_IDS` | `Dict[str, List[str]]` | Slot ID lists per day |
| `CONSTRAINTS` | `List[ConstraintBase]` | All added constraints |

### Endpoints

#### `POST /structure`
Creates the timetable time-grid. **Must be called before adding constraints or solving.**

**Body**:
```json
{
  "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  "day_start_time": "09:00",
  "day_end_time": "16:30",
  "lecture_duration_minutes": 55,
  "breaks": [
    {"label": "Morning Break", "start_time": "10:50", "end_time": "11:05"},
    {"label": "Lunch", "start_time": "12:50", "end_time": "13:45"}
  ]
}
```

**Response**:
```json
{"status": "structure_created", "days": ["Monday", ...], "slot_count": 35}
```

---

#### `POST /constraints`
Add a single constraint.

**Body**: Any constraint JSON (see Section 4). Resets if invalid type.

**Response**:
```json
{"status": "constraint_added", "constraint_id": "FAC_001", "total_constraints": 1}
```

---

#### `POST /constraints/batch`
Add multiple constraints at once.

**Body**: Array of constraint objects.

**Response**:
```json
{
  "status": "batch_processed",
  "added": 80,
  "failed": 1,
  "constraint_ids": ["FAC_001", ...],
  "errors": ["Item 5: Invalid constraint_type at index 5"]
}
```

---

#### `POST /constraints/validate`
Checks all stored constraints for structural correctness (no duplicate IDs, no empty parameters).

---

#### `GET /constraints`
Returns all stored constraints.

---

#### `DELETE /constraints`
Clears all constraints.

---

#### `POST /solve`
Runs the CP-SAT solver with the current structure and constraints.

**Returns**: Full solver result (see Section 5.6).

**Errors**: 
- 400 if structure not created
- 400 if no constraints added

---

#### `GET /status`
Returns current system state.

**Response**:
```json
{
  "structure_created": true,
  "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  "total_slots": 35,
  "constraint_count": 81,
  "hard_constraints": 79,
  "soft_constraints": 2
}
```

---

#### `POST /reset`
Clears all state (structure, slot IDs, constraints).

---

## 9. Data Pipeline (Real Data Workflow)

### Step 1: Extract from Excel

```bash
python scripts/extract_real_constraints.py
```

Reads `AY 2025_2026 ODD SUBJECT ALLOTMENT_JULY 2025.xlsx`, extracts:
- Faculty details → `data/real/faculty_constraints.json`
- Course/subject details → `data/real/course_constraints.json`
- Room info → `data/real/room_constraints.json`
- Special events → `data/real/special_constraints.json`
- All combined → `data/real/all_constraints_fixed.json`

Real data statistics: **38 faculties, 25 courses, 99 assignments, 16 rooms, 81 total constraints**

### Step 2: Start Server

```bash
python run.py server
# OR
uvicorn app.main:app --reload
```

### Step 3: Load Data via Client

```bash
python scripts/load_real_data.py
```

Sends extracted constraints to the running API server via HTTP.

### Automated Orchestration

```bash
python app/run_real_data.py
```

Runs Steps 1 and 3 automatically, pausing for user to start the server between steps.

### Full CLI Launcher (`run.py`)

```bash
python run.py server                        # Start FastAPI server
python run.py client status                # GET /status
python run.py client workflow <struct.json> <constraint.json>  # Full workflow
python run.py test                          # Run pytest
python run.py install                       # pip install -r requirements.txt
python run.py clean                         # Remove __pycache__
```

---

## 10. HTML Timetable Output

Several scripts in `scripts/` generate HTML timetable views from solver output JSON:

| Script | Output | Description |
|---|---|---|
| `simple_timetable_viewer.py` | `timetable_simple.html` | Clean simple HTML view |
| `visual_timetable.py` | `visual_timetable.html` | Color-coded visual timetable |
| `visual_timetable_real.py` | HTML | Visual view using real extracted data |
| `visual_with_names.py` | `timetable_with_names.html` | Shows faculty names in cells |
| `section_wise_timetable.py` | `section_wise_timetable.html` | Per-section view |
| `format_timetable.py` | Text/HTML | Generic formatter |
| `extract_master_timetable.py` | `master_timetable_data.json` + HTML | Full master view |

---

## 11. Constraint Validation Rules

`app/constraints/validator.py` enforces:
1. **Non-empty list**: At least one constraint must exist when validating.
2. **No duplicate IDs**: `constraint_id` must be globally unique across all constraints.
3. **Non-empty parameters**: Every constraint must have a non-empty `parameters` dict.

---

## 12. Key Design Decisions & Notes for AI Agents

1. **CP-SAT (not MIP)**: The solver uses Boolean Satisfiability (SAT-based CP) not linear programming. All decision variables are `BoolVar`. Sums must be over Python lists of `IntVar` objects, not plain integers.

2. **Separation of concerns**: The `app/core/` layer knows nothing about scheduling logic. It only generates the time grid. All scheduling intelligence is in `app/solver/`.

3. **Constraint type dual-dispatch**: `apply_constraint()` in `constraints.py` first checks `constraint_type` string, then falls back to `isinstance()` checks for backward compatibility.

4. **In-memory state**: The API maintains **no database**. State is lost on server restart. All data must be re-loaded after every server restart.

5. **Slot ID filtering**: Only slots with `'L'` in the slot_id are valid lecture slots and get solver variables. Break slots are excluded from all solver logic.

6. **Faculty–Course linkage**: A faculty can only be assigned to a course if their `faculty_id` appears in the course's `faculty_ids` list. This is enforced during variable creation.

7. **Section isolation**: Courses belong to sections (e.g., `"A"`, `"B"`, `"COMMON"`). The solver ensures no two courses in the same section overlap in time.

8. **Objective is maximization**: The solver tries to fill as many lecture slots as possible. If constraints are too tight (infeasible), it returns `status: "infeasible"` with no assignments.

9. **60-second solver timeout**: If an optimal solution isn't found in 60 seconds, it returns the best feasible solution found so far, or `infeasible` if none.

10. **Special constraints** block institutional reserved slots (Industry Talks, Proctor Meetings) from ever being used for regular classes by forcing their variables to 0.

---

## 13. Example: End-to-End Workflow

```python
import requests

BASE = "http://localhost:8000"

# Step 1: Create time structure
requests.post(f"{BASE}/structure", json={
    "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "day_start_time": "09:00",
    "day_end_time": "16:30",
    "lecture_duration_minutes": 55,
    "breaks": [
        {"label": "Lunch", "start_time": "12:50", "end_time": "13:45"}
    ]
})

# Step 2: Add faculty constraint
requests.post(f"{BASE}/constraints", json={
    "constraint_id": "FAC_001",
    "constraint_type": "faculty",
    "hardness": "hard",
    "parameters": {
        "faculty_id": "F001",
        "faculty_name": "Dr. Smith",
        "max_hours_per_week": 15,
        "available_days": ["Monday", "Wednesday", "Friday"]
    }
})

# Step 3: Add subject constraint
requests.post(f"{BASE}/constraints", json={
    "constraint_id": "SUB_CS101",
    "constraint_type": "subject",
    "hardness": "hard",
    "parameters": {
        "course_id": "CS101",
        "course_code": "CS101",
        "course_name": "Data Structures",
        "section": "A",
        "type": "theory",
        "weekly_lectures": 3,
        "faculty_ids": ["F001"]
    }
})

# Step 4: Solve
result = requests.post(f"{BASE}/solve").json()
print(result["status"])          # "feasible"
print(result["assignments"])     # slot_id → assignment info
```

---

## 14. Known Limitations / Future Work

- **Room assignment not implemented in solver**: Room constraints are registered but the model doesn't currently track which room a course is assigned to. Room capacity and type matching is logged but not enforced in the CP-SAT model.
- **Lab consecutive slots**: `add_lab_consecutive_slots_constraint()` is registered but only partially implemented (increments a counter; the actual implication constraint is commented out).
- **`apply_faculty_constraint()`**: The faculty constraint dispatcher function is a stub (`pass`) — faculty availability is instead enforced directly within `EnhancedTimetableModel._add_faculty_availability_constraints()`.
- **No persistent storage**: All state is in-memory. Restart = reset.
- **`constants.py`** is an empty placeholder.
- **`store.py`** in constraints is a placeholder (127 bytes).
- **`docs/api.md` and `docs/examples.md`**: Both empty files.
