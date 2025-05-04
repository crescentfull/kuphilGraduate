from .base import BaseRequirements

class Requirements2025(BaseRequirements):
    """2025년 이후 입학생들의 졸업요건"""
    
    # 공통 필수 과목
    COMMON_REQUIRED = {
        '심교': [
            '철학산책',  # 철학의 이해
        ],
        '지교': 5  # 문과대학 지정교양 과목 총 5개 이수
    }
    
    # 지교 필수 과목 (전공인정 가능한 지교 과목들)
    DESIGNATED_REQUIRED = [
        '철학의문제들',
        '동양사상과현실문제',
        '논리학'
    ]
    
    # 전공 기초 과목
    MAJOR_BASE = [
        '동양철학산책',
        '서양철학산책',
        '서양철학고전읽기',
        '서양고중세철학',
        '동양철학고전읽기'
    ]
    
    # 학술답사 과목
    FIELD_TRIP = [
        '학술답사Ⅰ',
        '학술답사Ⅱ',
        '학술답사Ⅲ'
    ]
    
    # 전공 선택 필수 과목 (5개 중 3개 이상)
    MAJOR_ELECTIVE = [
        '서양근세철학',
        '중국철학의이해',
        '서양현대철학',  # 현대철학
        '윤리학',
        '인식론',
        '형이상학',
        '한국철학의이해'
    ]
    
    MAJOR_ELECTIVE_MIN = 3  # 전공 선택 필수 과목 중 최소 이수 과목 수
    MAJOR_BASE_MIN = 5      # 전공 기초 과목 최소 이수 과목 수
    
    REQUIREMENTS = {
        'normal': {  # 심화전공자(주전공)
            'total_credits': 124,
            'common_required': COMMON_REQUIRED,
            'designated_required': DESIGNATED_REQUIRED,  # 지교 필수 과목 추가
            'major_base': MAJOR_BASE,
            'major_base_min': MAJOR_BASE_MIN,
            'major_elective': MAJOR_ELECTIVE,
            'major_elective_min': MAJOR_ELECTIVE_MIN,
            'field_trip': FIELD_TRIP,
            'field_trip_min': 2  # 학술답사 최소 이수 과목 수
        },
        'transfer': {
            'total_credits': 65,
            'common_required': {},
            'designated_required': DESIGNATED_REQUIRED,  # 지교 필수 과목 추가
            'major_base': MAJOR_BASE,
            'major_base_min': 2,
            'major_elective': MAJOR_ELECTIVE,
            'major_elective_min': 1,
            'field_trip': FIELD_TRIP,
            'field_trip_min': 1
        },
        'double': {
            'total_credits': 40,
            'common_required': {
                '심교': ['철학산책']
            },
            'designated_required': DESIGNATED_REQUIRED,  # 지교 필수 과목 추가
            'major_base': MAJOR_BASE,
            'major_base_min': 2,  # 전공 기초 과목 중 2개 이상
            'major_elective': MAJOR_ELECTIVE,
            'major_elective_min': 2  # 전공 선택 과목 중 2개 이상
        },
        'minor': {
            'total_credits': 21,
            'common_required': {},
            'designated_required': DESIGNATED_REQUIRED,  # 지교 필수 과목 추가
            'major_base': [
                '철학의문제들',
                '논리학'
            ],
            'major_base_min': 2,
            'major_elective': MAJOR_ELECTIVE,
            'major_elective_min': 1
        }
    } 