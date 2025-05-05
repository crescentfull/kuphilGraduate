from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from ..config.requirements.year_2024 import Requirements2024
from ..config.requirements.year_2025 import Requirements2025

@dataclass
class YearRequirement:
    year: int
    common_required: Dict[str, List[str]]
    designated_required: List[str]  # 지교(전공인정) 필수 과목
    major_required: List[str]
    major_elective_required: List[str]
    major_elective_min: int
    major_base: List[str]          # 전공 기초 과목
    major_base_min: int            # 전공 기초 과목 최소 이수 수
    total_credits: int
    internship_required: bool = False
    field_trip: List[str] = None
    field_trip_min: int = 0

class GraduationRequirementManager:
    def __init__(self):
        self.requirements = {
            2024: Requirements2024,
            2025: Requirements2025
        }

    def get_requirement(self, admission_year: int, student_type: str) -> Optional[YearRequirement]:
        """입학년도와 학생 유형에 따른 졸업요건을 반환"""
        try:
            # 2025년 이후 입학생은 2025년 요건 적용
            if admission_year >= 2025:
                requirement_class = self.requirements[2025]
            # 2024년 이전 입학생은 2024년 요건 적용
            else:
                requirement_class = self.requirements[2024]

            cfg = requirement_class.get_requirements(student_type)
            # YearRequirement dataclass로 매핑하여 반환
            return YearRequirement(
                year=admission_year,
                common_required=cfg['common_required'],
                designated_required=cfg.get('designated_required', []),
                major_required=cfg.get('major_required', []),
                major_elective_required=cfg.get('major_elective_required', []),
                major_elective_min=cfg.get('major_elective_min', 0),
                major_base=cfg.get('major_base', []),
                major_base_min=cfg.get('major_base_min', 0),
                total_credits=cfg['total_credits'],
                internship_required=cfg.get('internship_required', False),
                field_trip=cfg.get('field_trip', []),
                field_trip_min=cfg.get('field_trip_min', 0)
            )

        except KeyError:
            return None  # 해당 연도/유형 요건이 없으면 None 반환