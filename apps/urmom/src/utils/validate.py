import re
from typing import Any, List


class Validation:
    @staticmethod
    def validate_time_fmt(time_str: Any) -> str:
        """Validate if the time string is in HH:MM format."""

        pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
        if isinstance(time_str, str) and re.match(pattern, time_str):
            return time_str
        else:
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM format.")

    @staticmethod
    def validate_non_empty_list(input_list: Any) -> List[Any]:
        """Check if the input is a non-empty list."""
        if isinstance(input_list, list) and len(input_list) > 0:
            return input_list
        else:
            raise ValueError("Input is not a non-empty list.")
