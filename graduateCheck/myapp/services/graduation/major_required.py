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
        # 결과 구조 초기화
        result = {'required_courses': {}, 'missing_courses': {}, 'details': {}}
        category = '전공선택'

        # 1) 전공필수(list-based)
        for course in requirement.major_required:
            display = context.get_display_course_name(course)
            course_df = df[
                df['course_name'].str.contains(course, case=False, na=False) &
                (df['course_type'] == category)
            ]
            if not course_df.empty:
                credit = course_df['credits'].iloc[0]
                result['required_courses'].setdefault(category, []).append({
                    'course_name': display, 
                    'category': category, 
                    'credits': credit
                })
            else:
                credit = context.get_course_credit(course)
                result['missing_courses'].setdefault(category, []).append({
                    'course_name': display, 
                    'category': category, 
                    'credits': credit
                })

        # 2) 전공선택필수(count-based)
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
        eligible_df = df[df['course_type'] == category]
        if min_required is not None and completed_count >= min_required:
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