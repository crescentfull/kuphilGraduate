from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext

# --- 전공 필수 분석기 ---
class MajorRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement, student_type: str, context: AnalyzeContext):
        """업로드된 성적 데이터에서 지교 및 전공필수 과목 이수 여부를 판별합니다."""
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        # 1) 지교(전공인정) 과목 처리
        for course in requirement.designated_required:
            display_name = context.get_display_course_name(course)
            # 과목명 매핑 후 데이터 필터링
            course_data = df[df['course_name'].str.contains(course, case=False, na=False)]
            category = '지교'
            if not course_data.empty:
                credit = course_data['credits'].iloc[0]
                result['required_courses'].setdefault(category, []).append({
                    'course_name': display_name,
                    'category': category,
                    'credits': credit,
                    'necessary': True
                })
            else:
                credit = context.get_course_credit(course)
                result['missing_courses'].setdefault(category, []).append({
                    'course_name': display_name,
                    'category': category,
                    'credits': credit,
                    'necessary': False
                })

        # 2) 전공필수 과목 처리
        for course in requirement.major_required:
            display_name = context.get_display_course_name(course)
            # 전공필수 이수구분으로 필터링
            course_data = df[
                (df['course_name'].str.contains(course, case=False, na=False)) &
                (df['course_type'] == '전공선택')
            ]
            category = '전공선택'
            if not course_data.empty:
                credit = course_data['credits'].iloc[0]
                result['required_courses'].setdefault(category, []).append({
                    'course_name': display_name,
                    'category': category,
                    'credits': credit,
                    'necessary': True
                })
            else:
                credit = context.get_course_credit(course)
                result['missing_courses'].setdefault(category, []).append({
                    'course_name': display_name,
                    'category': category,
                    'credits': credit,
                    'necessary': False,
                })
        return result 