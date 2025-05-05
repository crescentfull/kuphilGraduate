class BaseRequirements:
    """기본 졸업요건 클래스"""
    
    TOTAL_CREDITS = 124  # 기본 졸업 이수학점
    
    # 공통 필수과목 (심교, 지교 등)
    COMMON_REQUIRED = {}
    
    # 지교 (전공) 필수
    DESIGNATED_REQUIRED = []
    
    # 전공 필수 이수과목
    MAJOR_REQUIRED = []
    
    # 전공 선택 최소 이수과목 수
    MAJOR_ELECTIVE_MIN = 0
    
    # 인턴십 필수 여부
    INTERNSHIP_REQUIRED = False
    
    @classmethod
    def get_requirements(cls, student_type: str) -> dict:
        """
        student_type별 요건 설정을 기본값과 병합하여 반환합니다.
        """
        # 기본 졸업요건
        base = {
            'total_credits': cls.TOTAL_CREDITS,
            'common_required': cls.COMMON_REQUIRED,
            'designated_required': cls.DESIGNATED_REQUIRED,
            'major_required': cls.MAJOR_REQUIRED,
            'major_elective_required': getattr(cls, 'MAJOR_ELECTIVE_REQUIRED', []),
            'major_elective_min': cls.MAJOR_ELECTIVE_MIN,
            'internship_required': cls.INTERNSHIP_REQUIRED,
            'field_trip': getattr(cls, 'FIELD_TRIP', []),
            'field_trip_min': getattr(cls, 'FIELD_TRIP_MIN', 0),
        }
        # 연도별 클래스(REQUIREMENTS)에서 타입별 오버라이드 항목 가져오기
        overrides = getattr(cls, 'REQUIREMENTS', {}).get(student_type, {})
        # 병합된 결과 반환
        merged = {**base, **overrides}
        return merged 