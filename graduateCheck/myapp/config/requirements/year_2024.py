from .base import BaseRequirements

class Requirements2024(BaseRequirements):
    """2024년 이전 입학생들의 졸업요건"""
    
    # 공통 필수 과목
    COMMON_REQUIRED = {
        '심교': [
            '철학산책',  # 철학의 이해
        ],
        '지교': 5  # 문과대학 지정교양 과목 총 5개 이수 (철학과 지정교양 3개 포함)
    }
    
    # 지교 필수 과목 (전공인정 가능한 지교 과목들)
    DESIGNATED_REQUIRED = [
        '철학의문제들',
        '동양사상과현실문제',
        '논리학'
    ]
    
    # 전공 선택 중 필수 이수 과목
    MAJOR_REQUIRED = [
        '서양철학고전읽기',
        '동양철학고전읽기',
        '서양고중세철학'  # 서양고대철학
    ]
    
    # 학술답사 과목
    FIELD_TRIP = [
        '학술답사Ⅰ',
        '학술답사Ⅱ',
        '학술답사Ⅲ'
    ]
    
    # 전공 선택 중 (7개 중 4개 이상) 필수 이수 과목
    MAJOR_ELECTIVE_REQUIRED = [
        '중국철학의이해',
        '윤리학',
        '서양근세철학',
        '인식론',
        '형이상학',
        '한국철학의이해',
        '서양현대철학'  # 현대철학
    ]
    
    MAJOR_ELECTIVE_MIN = 4  # 전공 선택 필수 과목 중 최소 이수 과목 수
    INTERNSHIP_REQUIRED = True  # 2017~2020학번 인턴십 의무

    REQUIREMENTS = {
        'normal': {
            'total_credits': 124,
            'common_required': COMMON_REQUIRED,
            'designated_required': DESIGNATED_REQUIRED,
            'major_required': MAJOR_REQUIRED,
            'major_elective_required': MAJOR_ELECTIVE_REQUIRED,
            'major_elective_min': MAJOR_ELECTIVE_MIN,
            'internship_required': INTERNSHIP_REQUIRED,
            'field_trip': FIELD_TRIP,
            'field_trip_min': 2
        },
        'transfer': {
            'total_credits': 65,
            'common_required': {},
            'designated_required': DESIGNATED_REQUIRED,
            'major_required': [
                '서양고중세철학',
                '중국철학의이해',
                '서양근세철학',
                '한국철학의이해',
                ],
            'major_elective_required': [
                '윤리학',
                '인식론',
                '형이상학',
                '서양현대철학',
                '중국유학',
            ],
            'major_elective_min': 3,
            'field_trip': FIELD_TRIP,
            'field_trip_min': 2,
            'internship_required': False
        },
        'double': {
            'total_credits': 40,
            'common_required': {
                '심교': ['철학산책']
            },
            'designated_required': DESIGNATED_REQUIRED,
            'major_required': [],
            'major_elective_required': MAJOR_ELECTIVE_REQUIRED,
            'major_elective_min': 4,
            'internship_required': False
        },
        'minor': {
            'total_credits': 24,
            'common_required': {},
            'designated_required': [],
            'major_required': [],
            'major_elective_required': [],
            'major_elective_min': 0,
            'internship_required': False
        }
    }

    @classmethod
    def get_requirements(cls, student_type: str):
        """
        BaseRequirements의 기본값을 받아온 뒤, student_type별 오버라이드를 적용합니다.
        """
        return super().get_requirements(student_type)  # base에서 모든 필드를 병합해줌 