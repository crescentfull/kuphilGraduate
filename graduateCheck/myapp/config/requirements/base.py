class BaseRequirements:
    """기본 졸업요건 클래스"""
    
    TOTAL_CREDITS = 124  # 기본 졸업 이수학점
    
    # 공통 필수과목 (심교, 지교 등)
    COMMON_REQUIRED = {}
    
    DESIGNATED_REQUIRED = []
    
    # 전공 필수과목
    MAJOR_REQUIRED = []
    
    # 전공 선택 최소 이수과목 수
    MAJOR_ELECTIVE_MIN = 0
    
    # 인턴십 필수 여부
    INTERNSHIP_REQUIRED = False
    
    @classmethod
    def get_requirements(cls):
        """졸업요건 반환"""
        return {
            'total_credits': cls.TOTAL_CREDITS,
            'common_required': cls.COMMON_REQUIRED,
            'designated_required': cls.DESIGNATED_REQUIRED,
            'major_required': cls.MAJOR_REQUIRED,
            'major_elective_min': cls.MAJOR_ELECTIVE_MIN,
            'internship_required': cls.INTERNSHIP_REQUIRED
        } 