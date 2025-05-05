from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext

# --- 학술답사 분석기 ---
class FieldTripAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement, student_type: str, context: AnalyzeContext):
        # 2017학번 이후 ~ 2024학번까지만 학술답사 요건 적용
        if context.admission_year is None or context.admission_year < 2017 or context.admission_year > 2024:
            return {
                'required_courses': {},
                'missing_courses': {},
            }
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        # 필드 트립 설정이 있는지 확인
        field_trip = requirement.field_trip or []
        field_trip_min = requirement.field_trip_min
        internship_required = requirement.internship_required
        if internship_required:
            field_trip_min = 1
        completed_field_trips = []
        for course in field_trip:
            course_name = course
            for old_name, new_name in self.course_name_mapping.items():
                if old_name == course:
                    course_name = new_name
                    break
            course_data = df[
                (df['course_name'] == course_name) &
                (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필'])) &
                (~df['grade'].isin(['F', 'NP']))
            ]
            if not course_data.empty:
                completed_field_trips.append({
                    'course_name': context.get_display_course_name(course),
                    'category': '학술답사',
                    'credits': course_data['credits'].iloc[0]
                })
        if len(completed_field_trips) >= field_trip_min:
            if '학술답사' not in result['required_courses']:
                result['required_courses']['학술답사'] = []
            result['required_courses']['학술답사'].extend(completed_field_trips)
        else:
            if field_trip_min > 0:
                missing_count = field_trip_min - len(completed_field_trips)
                missing_message = f"학술답사 {missing_count}개 더 이수 필요"
                if '학술답사' not in result['missing_courses']:
                    result['missing_courses']['학술답사'] = []
                result['missing_courses']['학술답사'].append({
                    'course_name': missing_message,
                    'category': '학술답사',
                    'credits': missing_count * context.get_course_credit('학술답사')
                })
                if completed_field_trips:
                    if '학술답사' not in result['required_courses']:
                        result['required_courses']['학술답사'] = []
                    result['required_courses']['학술답사'].extend(completed_field_trips)
        return result 