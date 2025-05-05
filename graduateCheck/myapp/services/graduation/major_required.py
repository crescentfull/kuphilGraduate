from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext

# --- 전공 필수/선택 분석기 ---
class MajorRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping
    
    def _process_course(self, course: str, is_designated: bool, df: pd.DataFrame, context: AnalyzeContext, result: dict) -> bool:
        """
        과목 처리 공통 로직을 추출한 헬퍼 함수
        is_designated: 지교로 이수 가능한 과목인지 여부
        """
        if is_designated:
            course_data = df[
                (df['course_name'].str.contains(course, case=False, na=False)) &
                (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
            ]
            if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                actual_category = '지교'
                original_type = '지교(전공인정)'
            else:
                actual_category = '전공'
                original_type = None
        else:
            course_data = df[
                (df['course_name'].str.contains(course, case=False, na=False)) &
                (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
            ]
            actual_category = '전공'
            original_type = None
        
        if not course_data.empty:
            if actual_category not in result['required_courses']:
                result['required_courses'][actual_category] = []
            result['required_courses'][actual_category].append({
                'course_name': context.get_display_course_name(course),
                'category': actual_category,
                'credits': course_data['credits'].iloc[0],
                'original_type': original_type or course_data['course_type'].iloc[0]
            })
            
            if actual_category == '지교':
                if '지교' not in result['required_courses']:
                    result['required_courses']['지교'] = []
                result['required_courses']['지교'].append({
                    'course_name': context.get_display_course_name(course),
                    'category': '지교',
                    'credits': course_data['credits'].iloc[0],
                    'original_type': original_type
                })
            return True
        else:
            if actual_category not in result['missing_courses']:
                result['missing_courses'][actual_category] = []
            result['missing_courses'][actual_category].append({
                'course_name': context.get_display_course_name(course),
                'category': actual_category,
                'credits': context.get_course_credit(course)
            })
            return False

    def _process_elective_course(self, course: str, is_designated: bool, df: pd.DataFrame, context: AnalyzeContext):
        """
        전공선택 과목 처리를 위한 헬퍼 함수
        """
        if is_designated:
            course_data = df[
                (df['course_name'].str.contains(course, case=False, na=False)) &
                (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
            ]
            if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                actual_category = '지교'
                original_type = '지교(전공선택인정)'
            else:
                actual_category = '전공선택'
                original_type = None
        else:
            course_data = df[
                (df['course_name'].str.contains(course, case=False, na=False)) &
                (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
            ]
            actual_category = '전공선택'
            original_type = None
        
        if not course_data.empty:
            elective_info = {
                'course_name': context.get_display_course_name(course),
                'category': actual_category,
                'credits': course_data['credits'].iloc[0],
                'original_type': original_type or course_data['course_type'].iloc[0]
            }
            
            if actual_category == '지교':
                return elective_info, {
                    'course_name': context.get_display_course_name(course),
                    'category': '지교',
                    'credits': course_data['credits'].iloc[0],
                    'original_type': original_type
                }
            return elective_info, None
        return None, None

    def analyze(self, df: pd.DataFrame, requirement: Any, student_type: str, context: AnalyzeContext) -> dict:
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        
        designated_required = requirement.get('designated_required', [])
        
        if 'major_required' in requirement:
            for course in requirement['major_required']:
                self._process_course(course, course in designated_required, df, context, result)
        
        if 'major_elective_required' in requirement:
            electives = requirement['major_elective_required']
            min_count = requirement['major_elective_min']
            completed = []
            for course in electives:
                info, designated_info = self._process_elective_course(course, course in designated_required, df, context)
                if info:
                    completed.append(info)
                    if designated_info:
                        if '지교' not in result['required_courses']:
                            result['required_courses']['지교'] = []
                        result['required_courses']['지교'].append(designated_info)
            if len(completed) >= min_count:
                result.setdefault('required_courses', {})
                result['required_courses'].setdefault('전공선택', []).extend(completed)
            else:
                missing = min_count - len(completed)
                result.setdefault('missing_courses', {})
                result['missing_courses'].setdefault('전공선택', []).append({
                    'course_name': f"전공선택필수 과목 중 {missing}개 더 이수 필요",
                    'category': '전공선택',
                    'credits': missing * context.get_course_credit('전공선택')
                })
                if completed:
                    result['required_courses'].setdefault('전공선택', []).extend(completed)
        return result 