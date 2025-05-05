from typing import Callable
from dataclasses import dataclass

@dataclass
class AnalyzeContext:
    get_display_course_name: Callable[[str], str]
    get_course_credit: Callable[[str], int]
    admission_year: int = None
    internship_completed: str = None 