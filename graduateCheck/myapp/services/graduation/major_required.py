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
                result['required_courses'].setdefault(category, []).append({
                    'course_name': display, 
                    'category': category, 
                    'credits': credit
                })
            else:
                logger.warning(f"과목 '{display}' 미이수")
                credit = context.get_course_credit(course)
                result['missing_courses'].setdefault(category, []).append({
                    'course_name': display, 
                    'category': category, 
                    'credits': credit
                })

        # 2) 전공선택필수(count-based)
        logger.info("전공 선택 필수 과목 확인 중...")
        electives = requirement.major_elective_required
        min_required = requirement.major_elective_min
        # 이수된 전공선택필수 과목 개수 계산
        completed_count = sum(
            not df[
                df['course_name'].str.contains(c, case=False, na=False) &
                (df['course_type'] == category)
            ].empty
            for c in electives
        )
        logger.info(f"이수한 전공 선택 필수 과목 수: {completed_count}/{min_required}")
        
        eligible_df = df[df['course_type'] == category]
        if min_required is not None and completed_count >= min_required:
            logger.info("전공 선택 필수 과목 요건 충족")
            # 이수된 과목 required 등록
            for _, row in eligible_df.iterrows():
                if any(c in row['course_name'] for c in electives):
                    result['required_courses'].setdefault(category, []).append({
                        'course_name': context.get_display_course_name(row['course_name']),
                        'category': category, 
                        'credits': row['credits']
                    })
            result['details'][f'{category} 과목 수'] = f'{completed_count}/{min_required} (충족)'
        elif min_required is not None:
            logger.warning(f"전공 선택 필수 과목 요건 미충족: {completed_count}/{min_required}")
            # 부족 시 요약 entry & 상세 기록
            missing_count = min_required - completed_count
            result['missing_courses'][category] = [{
                'course_name': f'{category} 과목 {missing_count}개 더 필요',
                'category': category,
                'credits': missing_count * context.get_course_credit(category)
            }]
            if completed_count > 0:
                for _, row in eligible_df.iterrows():
                    if any(c in row['course_name'] for c in electives):
                        result['required_courses'].setdefault(category, []).append({
                            'course_name': context.get_display_course_name(row['course_name']),
                            'category': category, 
                            'credits': row['credits']
                        })
            result['details'][f'{category} 과목 수'] = f'{completed_count}/{min_required} (미충족)'
        return result