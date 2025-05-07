from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext
import logging

logger = logging.getLogger(__name__)

class CommonRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement, student_type: str, context: AnalyzeContext):
        logger.info("=== 공통 필수 과목 분석 시작 ===")
        logger.info(f"입력 데이터프레임 크기: {df.shape}")
        logger.info(f"요구사항: {requirement.common_required}")
        
        result = {
            'required_courses': {},
            'missing_courses': {},
            'details': {}
        }
        common_required = requirement.common_required
        for category, courses in common_required.items():
            # 공통 필수 과목 카테고리만 처리 (심교, 지교)
            synonyms = {
                '심교': ['심교', '핵교', '심화교양', '핵심교양'],
                '지교': ['지교', '지정교양'],
            }
            # 심교와 지교 카테고리만 처리
            if category not in synonyms:
                continue
            category_types = synonyms[category]
            logger.info(f"카테고리 '{category}' 처리 중...")
            logger.info(f"카테고리 타입: {category_types}")
            
            if isinstance(courses, list):
                logger.debug(f"Checking list-based common requirement for category {category}: {courses}")
                for course in courses:
                    logger.info(f"과목 '{course}' 확인 중...")
                    course_data = df[
                        (df['course_name'] == course) &
                        (df['course_type'].isin(category_types))
                    ]
                    if not course_data.empty:
                        logger.info(f"과목 '{course}' 이수 확인됨")
                        if category not in result['required_courses']:
                            result['required_courses'][category] = []
                        result['required_courses'][category].append({
                            'course_name': context.get_display_course_name(course),
                            'category': category,
                            'credits': course_data['credits'].iloc[0],
                            'original_type': course_data['course_type'].iloc[0]
                        })
                    else:
                        logger.warning(f"과목 '{course}' 미이수")
                        if category not in result['missing_courses']:
                            result['missing_courses'][category] = []
                        result['missing_courses'][category].append({
                            'course_name': context.get_display_course_name(course),
                            'category': category,
                            'credits': context.get_course_credit(category)
                        })
            elif isinstance(courses, int):
                logger.debug(f"Checking count-based common requirement for category {category}: {courses}")
                category_courses = df[df['course_type'].isin(category_types)]
                completed_count = len(category_courses)
                if completed_count >= courses:
                    logger.info(f"Fulfilled common requirement '{category}' with {completed_count}/{courses}")
                    if category not in result['required_courses']:
                        result['required_courses'][category] = []
                    for _, row in category_courses.iterrows():
                        result['required_courses'][category].append({
                            'course_name': context.get_display_course_name(row['course_name']),
                            'category': category,
                            'credits': row['credits'],
                            'original_type': row['course_type']
                        })
                    result['details'][f'{category} 과목 수'] = f'{completed_count}/{courses} (충족)'
                else:
                    logger.warning(f"Unfulfilled common requirement '{category}': {completed_count}/{courses}")
                    if category not in result['missing_courses']:
                        result['missing_courses'][category] = []
                    missing_count = courses - completed_count
                    result['missing_courses'][category].append({
                        'course_name': f'{category} 과목 {missing_count}개 더 필요',
                        'category': category,
                        'credits': missing_count * context.get_course_credit(category)
                    })
                    if completed_count > 0:
                        if category not in result['required_courses']:
                            result['required_courses'][category] = []
                        for _, row in category_courses.iterrows():
                            result['required_courses'][category].append({
                                'course_name': context.get_display_course_name(row['course_name']),
                                'category': category,
                                'credits': row['credits'],
                                'original_type': row['course_type']
                            })
                    result['details'][f'{category} 과목 수'] = f'{completed_count}/{courses} (미충족)'
        return result 