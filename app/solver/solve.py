"""
Solver execution module with enhanced results
"""

from typing import Dict, Any
from ortools.sat.python import cp_model
from app.solver.model import TimetableModel


class SolveResult:
    """
    Structured solver result container with course/faculty info
    """
    
    def __init__(self, status: str, result_dict: Dict[str, Any] = None):
        self.status = status
        self.result_dict = result_dict or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return self.result_dict


def solve_timetable(model_wrapper: TimetableModel) -> SolveResult:
    """
    Executes the CP-SAT solver and returns enhanced results
    """
    try:
        result = model_wrapper.solve()
        return SolveResult(
            status=result['status'],
            result_dict=result
        )
    except Exception as e:
        logger.error(f"Solver error: {e}")
        return SolveResult(
            status="error",
            result_dict={"error": str(e)}
        )