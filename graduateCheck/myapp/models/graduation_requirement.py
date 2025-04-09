from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from ..config.requirements.year_2024 import Requirements2024
from ..config.requirements.year_2025 import Requirements2025

@dataclass
class CourseRequirement:
    course_name: str
    credits: int
    category: str

@dataclass
class YearRequirement:
    year: int
    common_required: Dict[str, List[str]]
    major_required: List[str]
    major_elective_min: int
    total_credits: int
    internship_required: bool = False

class GraduationRequirementManager:
    def __init__(self):
        self.requirements = {
            2024: Requirements2024,
            2025: Requirements2025
        }

    def get_requirement(self, admission_year: int, student_type: str) -> Optional[Any]:
        """입학년도와 학생 유형에 따른 졸업요건을 반환"""
        try:
            # 2025년 이후 입학생은 2025년 요건 적용
            if admission_year >= 2025:
                requirement_class = self.requirements[2025]
            # 2024년 이전 입학생은 2024년 요건 적용
            else:
                requirement_class = self.requirements[2024]

            return requirement_class()

        except KeyError:
            return None 