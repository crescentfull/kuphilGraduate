from .base import BaseRequirements

class Requirements2025(BaseRequirements):
    """2025년 이후 입학생들의 졸업요건"""
    
    # 공통 필수 과목
    COMMON_REQUIRED = {
        '심교': [
            '철학산책'
        ],
        '지교': 5  # 문과대학 지정교양 과목 총 5개 이수
    }
    
    # 전공기초 과목
    MAJOR_BASE = [
        '철학의문제들',
        '동양사상과현실문제',
        '동양철학산책',
        '서양철학산책',
        '서양철학고전읽기',
        '논리학',
        '서양고중세철학',
        '동양철학고전읽기'
    ]
    
    # 전공선택 과목
    MAJOR_ELECTIVE = [
        '윤리학',
        '중국철학의이해',
        '인식론',
        '한국철학의이해',
        '형이상학',
        '서양근세철학',
        '서양현대철학'
    ]
    
    # 학술답사 과목
    FIELD_TRIP = [
        '학술답사Ⅰ',
        '학술답사Ⅱ',
        '학술답사Ⅲ'
    ]
    
    REQUIREMENTS = {
        'normal': {  # 심화전공자(주전공)
            'total_credits': 124,
            'common_required': COMMON_REQUIRED,
            'major_base_min': 5,  # 전공기초 5과목 이상
            'major_base': MAJOR_BASE,
            'major_elective_min': 4,  # 전공선택 4과목 이상
            'major_elective': MAJOR_ELECTIVE,
            'field_trip_min': 2,  # 학술답사 2과목 이상
            'field_trip': FIELD_TRIP,
            'internship_required': False
        },
        'transfer': {  # 제1전공 이수자
            'total_credits': 65,
            'common_required': COMMON_REQUIRED,
            'major_base_min': 3,  # 전공기초 3과목 이상
            'major_base': MAJOR_BASE,
            'major_elective_min': 3,  # 전공선택 3과목 이상
            'major_elective': MAJOR_ELECTIVE,
            'field_trip_min': 2,  # 학술답사 2과목 이상
            'field_trip': FIELD_TRIP,
            'internship_required': False
        },
        'double': {  # 제2전공 이수자(다전공자)
            'total_credits': 40,
            'common_required': COMMON_REQUIRED,
            'major_base_min': 3,  # 전공기초 3과목 이상
            'major_base': MAJOR_BASE,
            'major_elective_min': 3,  # 전공선택 3과목 이상
            'major_elective': MAJOR_ELECTIVE,
            'field_trip_min': 0,  # 학술답사 불필요
            'field_trip': [],
            'internship_required': False
        },
        'minor': {  # 부전공자
            'total_credits': 21,
            'common_required': COMMON_REQUIRED,
            'major_base_min': 2,  # 전공기초 2과목 이상
            'major_base': MAJOR_BASE,
            'major_elective_min': 15,  # 전공선택 15학점 이상
            'major_elective': MAJOR_ELECTIVE,
            'field_trip_min': 0,  # 학술답사 불필요
            'field_trip': [],
            'internship_required': False
        }
    } 