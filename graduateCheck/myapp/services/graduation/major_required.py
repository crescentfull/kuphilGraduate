from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext
import logging

logger = logging.getLogger(__name__)

# --- 전공 필수 분석기 ---
class MajorRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement, student_type: str, context: AnalyzeContext):
        """업로드된 성적 데이터에서 전공선택(전선) 과목만 판별합니다."""
        logger.info("=== 전공 필수 과목 분석 시작 ===")
        logger.info(f"전공 필수 과목: {requirement.major_required}")
        logger.info(f"전공 선택 필수 과목: {requirement.major_elective_required}")
        logger.info(f"전공 선택 최소 이수 과목 수: {requirement.major_elective_min}")
        
        # 결과 구조 초기화
        result = {'required_courses': {}, 'missing_courses': {}, 'details': {}}
        category = '전공선택'

        # 1) 전공필수(list-based)
        logger.info("전공 필수 과목 확인 중...")
        completed_major_required = []
        for course in requirement.major_required:
            display = context.get_display_course_name(course)
            logger.info(f"과목 '{display}' 확인 중...")
            course_df = df[
                df['course_name'].str.contains(course, case=False, na=False) &
                (df['course_type'] == category)
            ]
            
            if not course_df.empty:
                logger.info(f"과목 '{display}' 이수 확인됨")
                credit = course_df['credits'].iloc[0]
                completed_major_required.append({
                    'course_name': display, 
                    'category': category, 
                    'credits': credit,
                    'original_type': "필수"  # 전공 필수 과목으로 설정
                })
            else:
                logger.warning(f"과목 '{display}' 미이수")
                credit = context.get_course_credit(course)
                result['missing_courses'].setdefault(category, []).append({
                    'course_name': display, 
                    'category': category, 
                    'credits': credit,
                    'original_type': "필수"
                })
        
        # # 전공 필수 과목 이수 현황 업데이트
        # result['required_courses'].setdefault(category, []).extend(completed_major_required)
        # result['details'][f'{category} 필수 과목 수'] = f'{len(completed_major_required)}/{len(requirement.major_required)}'

        # 2) 전공선택필수(count-based)
        logger.info("전공 선택 필수 과목 확인 중...")
        electives = requirement.major_elective_required
        min_required = requirement.major_elective_min
        
        # 이수된 전공선택필수 과목 확인
        completed_courses = []
        missing_courses = []
        for course in electives:
            display = context.get_display_course_name(course)
            logger.info(f"과목 '{display}' 확인 중...")
            course_df = df[
                df['course_name'].str.contains(course, case=False, na=False) &
                (df['course_type'] == category)
            ]
            
            if not course_df.empty:
                logger.info(f"과목 '{display}' 이수 확인됨")
                credit = course_df['credits'].iloc[0]
                completed_courses.append({
                    'course_name': display,
                    'category': category,
                    'credits': credit,
                    'original_type': '전공선택'
                })
            else:
                logger.warning(f"과목 '{display}' 미이수")
                missing_courses.append({
                    'course_name': display,
                    'category': category,
                    'credits': context.get_course_credit(course)
                })
        
        # 이수 과목 수 확인
        completed_count = len(completed_courses)+len(completed_major_required)
        min_required = len(requirement.major_elective_required)
        logger.info(f"이수한 전공 선택 필수 과목 수: {completed_count}/{min_required}")
        
        is_fulfilled = completed_count >= min_required
        if is_fulfilled:
            logger.info("전공 선택 필수 과목 요건 충족")
            result['required_courses'].setdefault(category, []).extend(completed_courses)
            result['details'][f'{category} 과목 수'] = {
                'value': f'{completed_count}/{min_required}',
                'is_fulfilled': True
            }
        else:
            logger.warning(f"전공 선택 필수 과목 요건 미충족: {completed_count}/{min_required}")
            result['missing_courses'].setdefault(category, []).extend(missing_courses)
            if completed_courses:
                result['required_courses'].setdefault(category, []).extend(completed_courses)
            result['details'][f'{category} 과목 수'] = {
                'value': f'{completed_count}/{min_required}',
                'is_fulfilled': False
            }
        
        logger.info(f"전공 필수 과목 분석 완료: {result}")
        return result