"""
Defines time-related abstractions such as days, periods, and slot indexing.
Responsible for representing the temporal grid on which timetables are built.
"""

"""
Time slot abstraction utilities.

This module is responsible for:
- Generating stable, deterministic, unique slot IDs
- Distinguishing lecture slots from break slots
- Providing helper functions to query slot type and timing

This module contains NO scheduling, optimization, faculty, subject,
room, constraint, solver, or AI-related logic.
"""

from typing import Dict


def generate_slot_id(day: str, start_time: str, end_time: str, slot_type: str) -> str:
    """
    Generates a stable, unique slot ID based on day, time, and slot type.

    Example:
        MON_0900_1000_L
        MON_1100_1200_B

    :param day: Day name (e.g., "Monday")
    :param start_time: Slot start time in HH:MM
    :param end_time: Slot end time in HH:MM
    :param slot_type: Slot type ("lecture" or "break")
    :return: Deterministic slot ID string
    """
    assert slot_type in {"lecture", "break"}, f"Invalid slot_type: {slot_type}"

    day_code = day[:3].upper()
    start = start_time.replace(":", "")
    end = end_time.replace(":", "")
    type_code = "L" if slot_type == "lecture" else "B"

    return f"{day_code}_{start}_{end}_{type_code}"


def is_lecture_slot(slot: Dict[str, str]) -> bool:
    """
    Checks whether the given slot represents a lecture slot.

    :param slot: Slot dictionary
    :return: True if lecture slot, False otherwise
    """
    return slot.get("type") == "lecture"


def is_break_slot(slot: Dict[str, str]) -> bool:
    """
    Checks whether the given slot represents a break slot.

    :param slot: Slot dictionary
    :return: True if break slot, False otherwise
    """
    return slot.get("type") == "break"


def get_slot_start_time(slot: Dict[str, str]) -> str:
    """
    Retrieves the start time of a slot.

    :param slot: Slot dictionary
    :return: Start time in HH:MM format
    """
    return slot.get("start_time")


def get_slot_end_time(slot: Dict[str, str]) -> str:
    """
    Retrieves the end time of a slot.

    :param slot: Slot dictionary
    :return: End time in HH:MM format
    """
    return slot.get("end_time")