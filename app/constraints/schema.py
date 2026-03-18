from typing import Literal, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

# Define valid constraint types - MUST include "special"
ConstraintType = Literal["faculty", "subject", "room", "special"]

class ConstraintBase(BaseModel):
    constraint_id: str = Field(..., min_length=1)
    constraint_type: ConstraintType
    hardness: Literal["hard", "soft"]
    parameters: Dict[str, Any]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )


class FacultyConstraint(ConstraintBase):
    constraint_type: Literal["faculty"] = "faculty"


class SubjectConstraint(ConstraintBase):
    constraint_type: Literal["subject"] = "subject"


class RoomConstraint(ConstraintBase):
    constraint_type: Literal["room"] = "room"


class SpecialConstraint(ConstraintBase):
    constraint_type: Literal["special"] = "special"


# This helps with validation in the routes
AnyConstraint = Union[
    FacultyConstraint, 
    SubjectConstraint, 
    RoomConstraint, 
    SpecialConstraint
]