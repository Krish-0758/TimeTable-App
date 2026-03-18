from typing import List

from app.constraints.schema import ConstraintBase


def validate_constraints(constraints: List[ConstraintBase]) -> None:
    """
    Validates a list of constraint objects for basic structural correctness.

    Raises ValueError if validation fails.
    """
    if not constraints:
        raise ValueError("No constraints provided.")

    seen_ids = set()

    for constraint in constraints:
        if constraint.constraint_id in seen_ids:
            raise ValueError(
                f"Duplicate constraint_id detected: {constraint.constraint_id}"
            )
        seen_ids.add(constraint.constraint_id)

        if not constraint.parameters:
            raise ValueError(
                f"Constraint '{constraint.constraint_id}' has empty parameters."
            )