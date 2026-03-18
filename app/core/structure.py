"""
Core timetable structure module.

This module defines deterministic, JSON-serializable structures for
representing working days and generating daily time slots based on:
- Configurable working days
- Configurable start and end times
- Fixed lecture duration
- Fixed labeled breaks

This module contains NO scheduling, constraint, faculty, subject,
room, solver, or AI-related logic.
"""

from datetime import datetime, timedelta
from typing import List, Dict


class TimetableStructure:
    """
    Represents the base academic timetable structure and is responsible
    ONLY for deterministic time slot generation.
    """

    def __init__(
        self,
        working_days: List[str],
        day_start_time: str,
        day_end_time: str,
        lecture_duration_minutes: int,
        breaks: List[Dict[str, str]],
    ):
        self.working_days = working_days
        self.day_start_time = day_start_time
        self.day_end_time = day_end_time
        self.lecture_duration_minutes = lecture_duration_minutes
        self.breaks = breaks

    # -------------------------
    # Public API
    # -------------------------

    def generate(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Generates deterministic time slots for all working days.

        :return: Dictionary mapping day -> list of slot dictionaries
        """
        daily_slots = self._generate_daily_slots()

        return {
            day: list(daily_slots)
            for day in self.working_days
        }

    # ✅ REQUIRED PUBLIC ALIAS (FIX)
    def generate_week_structure(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Public alias used by API and solver layers.
        """
        return self.generate()

    # -------------------------
    # Internal helpers
    # -------------------------

    def _generate_daily_slots(self) -> List[Dict[str, str]]:
        """
        Deterministically generates time slots for a single day,
        respecting fixed breaks.
        """
        slots: List[Dict[str, str]] = []

        start = self._parse_time(self.day_start_time)
        end = self._parse_time(self.day_end_time)
        lecture_delta = timedelta(minutes=self.lecture_duration_minutes)

        break_windows = [
            {
                "label": b["label"],
                "start": self._parse_time(b["start_time"]),
                "end": self._parse_time(b["end_time"]),
            }
            for b in self.breaks
        ]

        current = start

        while current < end:
            active_break = next(
                (b for b in break_windows if b["start"] <= current < b["end"]),
                None,
            )

            if active_break:
                slots.append(
                    {
                        "type": "break",
                        "label": active_break["label"],
                        "start_time": self._format_time(active_break["start"]),
                        "end_time": self._format_time(active_break["end"]),
                    }
                )
                current = active_break["end"]
                continue

            if current + lecture_delta > end:
                break

            slot_end = current + lecture_delta

            slots.append(
                {
                    "type": "lecture",
                    "start_time": self._format_time(current),
                    "end_time": self._format_time(slot_end),
                }
            )

            current = slot_end

        return slots

    @staticmethod
    def _parse_time(time_str: str) -> datetime:
        return datetime.strptime(time_str, "%H:%M")

    @staticmethod
    def _format_time(time_obj: datetime) -> str:
        return time_obj.strftime("%H:%M")