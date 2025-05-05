from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext

class CommonRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement: Any, student_type: str, context: AnalyzeContext):
        result = {
            'required_courses': {},
            'missing_courses': {},
            'details': {}
        }
        common_required = requirement['common_required']
        for category, courses in common_required.items():
            # --- 이수구분 그룹 확장 ---
            if category in ['심화교양', '심교', '핵심교양', '핵교']:
                category_types = ['심화교양', '심교', '핵심교양', '핵교']
            elif category in ['기초교양', '기교']:
                category_types = ['기초교양', '기교']
            elif category in ['일반교양', '일교']:
                category_types = ['일반교양', '일교']
            elif category in ['지정교양', '지교']:
                category_types = ['지정교양', '지교']
            elif category in ['일반선택', '일선']:
                category_types = ['일반선택', '일선']
            else:
                category_types = [category]

            if isinstance(courses, list):
                for course in courses:
                    course_name = course
                    for old_name, new_name in self.course_name_mapping.items():
                        if old_name == course:
                            course_name = new_name
                            break
                    course_data = df[
                        (df['course_name'].str.contains(course, case=False, na=False)) & 
                        (df['course_type'].isin(category_types))
                    ]
                    if not course_data.empty:
                        if category not in result['required_courses']:
                            result['required_courses'][category] = []
                        result['required_courses'][category].append({
                            'course_name': context.get_display_course_name(course),
                            'category': category,
                            'credits': course_data['credits'].iloc[0]
                        })
                    else:
                        if category not in result['missing_courses']:
                            result['missing_courses'][category] = []
                        result['missing_courses'][category].append({
                            'course_name': context.get_display_course_name(course),
                            'category': category,
                            'credits': context.get_course_credit(course)
                        })
            elif isinstance(courses, int):
                category_courses = df[df['course_type'].isin(category_types)]
                completed_count = len(category_courses)
                if completed_count >= courses:
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