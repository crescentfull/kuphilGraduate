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
    
    # 전공 필수 과목
    MAJOR_REQUIRED = [
        '철학의문제들',
        '동양사상과현실문제',
        '논리학',
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
    
    # 전공 선택 필수 과목 (7개 중 4개 이상)
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
            'major_required': MAJOR_REQUIRED,
            'major_elective_required': MAJOR_ELECTIVE_REQUIRED,
            'major_elective_min': MAJOR_ELECTIVE_MIN,
            'internship_required': INTERNSHIP_REQUIRED,
            'field_trip': FIELD_TRIP,
            'field_trip_min': 2  # 학술답사 최소 이수 과목 수
        },
        'transfer': {
            'total_credits': 65,
            'common_required': {},
            'major_required': ['서양고중세철학'],
            'major_elective_required': MAJOR_ELECTIVE_REQUIRED,
            'major_elective_min': 1,  # 학술답사 중 1개 이상
            'major_elective_courses': [  # 전공 선택 과목 (5개 중 3개 이상)
                '중국철학의이해',
                '윤리학',
                '서양근세철학',
                '인식론',
                '형이상학',
                '한국철학의이해',
                '중국유학'  # 유가철학
            ],
            'major_elective_courses_min': 3,
            'field_trip': FIELD_TRIP,
            'field_trip_min': 1,
            'internship_required': False
        },
        'double': {
            'total_credits': 40,
            'common_required': {
                '심교': ['철학산책']
            },
            'major_required': [],
            'major_elective_required': [
                '서양고중세철학',
                '중국철학의이해',
                '윤리학',
                '인식론',
                '서양근세철학',
                '한국철학의이해',
                '형이상학'
            ],
            'major_elective_min': 4,
            'internship_required': False
        },
        'minor': {
            'total_credits': 21,
            'common_required': {},
            'major_required': [
                '철학의문제들',
                '논리학'
            ],
            'major_elective_required': [
                '중국철학의이해',
                '윤리학',
                '서양근세철학',
                '인식론',
                '형이상학',
                '한국철학의이해',
                '서양현대철학'
            ],
            'major_elective_min': 3,
            'internship_required': False
        }
    } 