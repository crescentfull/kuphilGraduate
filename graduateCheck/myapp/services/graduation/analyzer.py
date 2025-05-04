from typing import Dict, Any, Callable
import pandas as pd
from dataclasses import dataclass
from ...models.graduation_requirement import GraduationRequirementManager
from ..excel.cleaner import clean_dataframe

@dataclass
class AnalyzeContext:
    get_display_course_name: Callable[[str], str]
    get_course_credit: Callable[[str], int]
    admission_year: int = None
    internship_completed: str = None

# --- 교양 필수 분석기 ---
class CommonRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement: Any, student_type: str, context: AnalyzeContext):
        result = {
            'required_courses': {},
            'missing_courses': {},
            'details': {}
        }
        common_required = requirement.REQUIREMENTS[student_type]['common_required']
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

# --- 전공 필수/선택 분석기 ---
class MajorRequiredAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement: Any, student_type: str, context: AnalyzeContext):
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        if 'major_required' in requirement.REQUIREMENTS[student_type]:
            major_required = requirement.REQUIREMENTS[student_type]['major_required']
            major_required_as_designated = [
                '철학의문제들',
                '동양사상과현실문제',
                '논리학'
            ]
            for course in major_required:
                if course in major_required_as_designated:
                    course_data = df[
                        (df['course_name'].str.contains(course, case=False, na=False)) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                    ]
                    actual_category = '전공'
                    if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                        actual_category = '지교(전공인정)'
                else:
                    course_data = df[
                        (df['course_name'].str.contains(course, case=False, na=False)) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    actual_category = '전공'
                if not course_data.empty:
                    if actual_category not in result['required_courses']:
                        result['required_courses'][actual_category] = []
                    result['required_courses'][actual_category].append({
                        'course_name': context.get_display_course_name(course),
                        'category': actual_category,
                        'credits': course_data['credits'].iloc[0],
                        'original_type': course_data['course_type'].iloc[0]
                    })
                else:
                    if actual_category not in result['missing_courses']:
                        result['missing_courses'][actual_category] = []
                    result['missing_courses'][actual_category].append({
                        'course_name': context.get_display_course_name(course),
                        'category': actual_category,
                        'credits': context.get_course_credit(course)
                    })
            # 전공 선택 필수 과목 체크 (2024년 요건)
            if 'major_elective_required' in requirement.REQUIREMENTS[student_type]:
                major_elective_required = requirement.REQUIREMENTS[student_type]['major_elective_required']
                major_elective_min = requirement.REQUIREMENTS[student_type]['major_elective_min']
                major_elective_as_designated = [
                    '윤리학',
                    '인식론',
                    '한국철학의이해'
                ]
                completed_electives = []
                for course in major_elective_required:
                    if course in major_elective_as_designated:
                        course_data = df[
                            (df['course_name'].str.contains(course, case=False, na=False)) &
                            (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                        ]
                        actual_category = '전공선택'
                        if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                            actual_category = '지교(전공선택인정)'
                    else:
                        course_data = df[
                            (df['course_name'].str.contains(course, case=False, na=False)) &
                            (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                        ]
                        actual_category = '전공선택'
                    if not course_data.empty:
                        completed_electives.append({
                            'course_name': context.get_display_course_name(course),
                            'category': actual_category,
                            'credits': course_data['credits'].iloc[0],
                            'original_type': course_data['course_type'].iloc[0]
                        })
                if len(completed_electives) >= major_elective_min:
                    if '전공선택' not in result['required_courses']:
                        result['required_courses']['전공선택'] = []
                    result['required_courses']['전공선택'].extend(completed_electives)
                else:
                    missing_count = major_elective_min - len(completed_electives)
                    missing_message = f"전공선택필수 과목 중 {missing_count}개 더 이수 필요"
                    if '전공선택' not in result['missing_courses']:
                        result['missing_courses']['전공선택'] = []
                    result['missing_courses']['전공선택'].append({
                        'course_name': missing_message,
                        'category': '전공선택',
                        'credits': missing_count * context.get_course_credit('전공선택')
                    })
                    if completed_electives:
                        if '전공선택' not in result['required_courses']:
                            result['required_courses']['전공선택'] = []
                        result['required_courses']['전공선택'].extend(completed_electives)
        return result

# --- 학술답사 분석기 ---
class FieldTripAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement: Any, student_type: str, context: AnalyzeContext):
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        if 'field_trip' in requirement.REQUIREMENTS[student_type] and requirement.REQUIREMENTS[student_type]['field_trip']:
            field_trip = requirement.REQUIREMENTS[student_type]['field_trip']
            field_trip_min = requirement.REQUIREMENTS[student_type]['field_trip_min']
            internship_required = requirement.REQUIREMENTS[student_type].get('internship_required', False)
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
                if (context.admission_year is not None and context.admission_year <= 2024 and len(completed_field_trips) == 1 and context.internship_completed == 'yes'):
                    if '학술답사' not in result['required_courses']:
                        result['required_courses']['학술답사'] = []
                    result['required_courses']['학술답사'].extend(completed_field_trips)
                    result['required_courses']['학술답사'].append({
                        'course_name': '인턴십',
                        'category': '학술답사',
                        'credits': 0
                    })
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

# --- 2025년 요건 분석기 ---
class Year2025RequirementAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement: Any, student_type: str, context: AnalyzeContext):
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        if 'major_base' in requirement.REQUIREMENTS[student_type]:
            major_base = requirement.REQUIREMENTS[student_type]['major_base']
            major_base_min = requirement.REQUIREMENTS[student_type]['major_base_min']
            major_base_as_designated = [
                '철학의문제들',
                '동양사상과현실문제',
                '논리학'
            ]
            completed_base = []
            for course in major_base:
                if course in major_base_as_designated:
                    course_data = df[
                        (df['course_name'] == course) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                    ]
                    actual_category = '전공기초'
                    if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                        actual_category = '지교(전공기초인정)'
                else:
                    course_data = df[
                        (df['course_name'] == course) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    actual_category = '전공기초'
                if not course_data.empty:
                    completed_base.append({
                        'course_name': context.get_display_course_name(course),
                        'category': actual_category,
                        'credits': course_data['credits'].iloc[0],
                        'original_type': course_data['course_type'].iloc[0]
                    })
            if len(completed_base) >= major_base_min:
                if '전공기초' not in result['required_courses']:
                    result['required_courses']['전공기초'] = []
                result['required_courses']['전공기초'].extend(completed_base)
            else:
                missing_count = major_base_min - len(completed_base)
                missing_message = f"전공기초 과목 중 {missing_count}개 더 이수 필요"
                if '전공기초' not in result['missing_courses']:
                    result['missing_courses']['전공기초'] = []
                result['missing_courses']['전공기초'].append({
                    'course_name': missing_message,
                    'category': '전공기초',
                    'credits': missing_count * context.get_course_credit('전공기초')
                })
                if completed_base:
                    if '전공기초' not in result['required_courses']:
                        result['required_courses']['전공기초'] = []
                    result['required_courses']['전공기초'].extend(completed_base)
        if 'major_elective' in requirement.REQUIREMENTS[student_type]:
            major_elective = requirement.REQUIREMENTS[student_type]['major_elective']
            major_elective_min = requirement.REQUIREMENTS[student_type]['major_elective_min']
            major_elective_as_designated = [
                '윤리학',
                '인식론',
                '한국철학의이해'
            ]
            completed_electives = []
            for course in major_elective:
                if course in major_elective_as_designated:
                    course_data = df[
                        (df['course_name'] == course) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                    ]
                    actual_category = '전공선택'
                    if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                        actual_category = '지교(전공선택인정)'
                else:
                    course_data = df[
                        (df['course_name'] == course) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    actual_category = '전공선택'
                if not course_data.empty:
                    completed_electives.append({
                        'course_name': context.get_display_course_name(course),
                        'category': actual_category,
                        'credits': course_data['credits'].iloc[0],
                        'original_type': course_data['course_type'].iloc[0]
                    })
            if len(completed_electives) >= major_elective_min:
                if '전공선택' not in result['required_courses']:
                    result['required_courses']['전공선택'] = []
                result['required_courses']['전공선택'].extend(completed_electives)
            else:
                missing_count = major_elective_min - len(completed_electives)
                missing_message = f"전공선택 과목 중 {missing_count}개 더 이수 필요"
                if '전공선택' not in result['missing_courses']:
                    result['missing_courses']['전공선택'] = []
                result['missing_courses']['전공선택'].append({
                    'course_name': missing_message,
                    'category': '전공선택',
                    'credits': missing_count * context.get_course_credit('전공선택')
                })
                if completed_electives:
                    if '전공선택' not in result['required_courses']:
                        result['required_courses']['전공선택'] = []
                    result['required_courses']['전공선택'].extend(completed_electives)
        if 'field_trip' in requirement.REQUIREMENTS[student_type] and requirement.REQUIREMENTS[student_type]['field_trip']:
            field_trip = requirement.REQUIREMENTS[student_type]['field_trip']
            field_trip_min = requirement.REQUIREMENTS[student_type]['field_trip_min']
            completed_field_trips = []
            for course in field_trip:
                course_data = df[
                    (df['course_name'] == course) &
                    (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
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

class GraduationAnalyzer:
    def __init__(self):
        self.requirement_manager = GraduationRequirementManager()
        
        # 과목명 매핑 (이전 과목명 -> 현재 과목명)
        self.course_name_mapping = {
            '철학의이해': '철학산책',
            '서양고대철학': '서양고중세철학',
            '현대철학': '서양현대철학',
            '유가철학': '중국유학'
        }
        
        # 과목 구분 매핑
        self.course_type_mapping = {
            '기교': '기초교양',
            '핵교': '핵심교양',
            '일교': '일반교양',
            '지교': '지정교양',
            '지필': '지정교양필수',
            '전선': '전공선택',
            '전필': '전공필수',
            '일선': '일반선택',
            '심교': '심화교양',
            '다선': '다전공선택',
            '다지': '다전공지교',
            '다필': '다전공필수',
        }
        self.common_required_analyzer = CommonRequiredAnalyzer(self.course_name_mapping)
        self.major_required_analyzer = MajorRequiredAnalyzer(self.course_name_mapping)
        self.field_trip_analyzer = FieldTripAnalyzer(self.course_name_mapping)
        self.year2025_requirement_analyzer = Year2025RequirementAnalyzer(self.course_name_mapping)

    def analyze(self, df: pd.DataFrame, student_type: str, admission_year: int, internship_completed: str = 'no') -> Dict[str, Any]:
        """졸업요건 분석 수행"""
        try:
            # 0. 원본 데이터의 총 학점 합계 확인
            original_total_credits = df['credits'].sum() if 'credits' in df.columns else 0
            print(f"원본 데이터 총 학점: {original_total_credits}")
            
            # 1. 데이터 정제
            df = clean_dataframe(df)
            
            # F학점 과목 추출
            f_grade_courses = []
            if 'grade' in df.columns:
                f_df = df[df['grade'].isin(['F', 'N'])]
                for _, row in f_df.iterrows():
                    f_grade_courses.append({
                        'course_name': row['course_name'],
                        'year': row.get('year', ''),
                        'semester': row.get('semester', ''),
                        'grade': row['grade'],
                        'credits': row['credits'],
                    })
            
            # 1.5 정제 후 총 학점 확인
            cleaned_total_credits = df['credits'].sum()
            print(f"정제 후 총 학점: {cleaned_total_credits}")
            
            # 2. 과목명 매핑 적용
            df = self._apply_course_name_mapping(df)
            
            # 3. 과목 구분 매핑 적용
            df = self._apply_course_type_mapping(df)
            
            # 3.5 매핑 후 총 학점 확인
            mapped_total_credits = df['credits'].sum()
            print(f"매핑 후 총 학점: {mapped_total_credits}")
            
            # 4. 졸업요건 가져오기
            requirement = self.requirement_manager.get_requirement(
                admission_year, 
                student_type
            )
            if not requirement:
                raise ValueError("해당하는 졸업요건을 찾을 수 없습니다.")
            
            # 5. 요건 분석
            result = self._analyze_requirements(df, requirement, student_type, admission_year, internship_completed)
            
            # 6. 입학년도 정보 추가
            result['admission_year'] = admission_year
            
            # 7. 인턴십 이수 여부 추가
            result['internship_completed'] = internship_completed == 'yes'
            print(f"인턴십 이수 여부: {result['internship_completed']}")
            
            # 8. 2024학번까지는 인턴십 이수 여부 확인
            if admission_year <= 2024 and not result['internship_completed']:
                result['status'] = '미달'
                result['missing_requirements'] = result.get('missing_requirements', [])
                result['missing_requirements'].append('인턴십 미이수')
            result['f_grade_courses'] = f_grade_courses
            return result
        except Exception as e:
            return {
                'error': str(e),
                'status': '오류',
            }

    def _apply_course_name_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        df['course_name'] = df['course_name'].str.replace(' ', '')
        
        # 매핑 적용
        for old_name, new_name in self.course_name_mapping.items():
            # 정확한 매칭
            df.loc[df['course_name'] == old_name, 'course_name'] = new_name
            
            # 부분 매칭 (과목명에 old_name이 포함된 경우)
            df.loc[df['course_name'].str.contains(old_name, case=False, na=False), 'course_name'] = new_name
        return df

    def _apply_course_type_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        for old_type, new_type in self.course_type_mapping.items():
            df.loc[df['course_type'] == old_type, 'course_type'] = new_type
        return df

    def _analyze_requirements(self, df: pd.DataFrame, requirement: Any, student_type: str, admission_year: int, internship_completed: str = 'no') -> Dict[str, Any]:
        """졸업요건 상세 분석"""
        # 총 이수학점 계산 (F 학점이나 취득학점포기 과목 제외)
        valid_credits = df[
            (df['grade'].notna()) & 
            (~df['grade'].isin(['F', 'NP']))
        ]['credits'].sum() if 'grade' in df.columns else df['credits'].sum()
        print(f"유효한 총 이수학점: {valid_credits}")
        
        # 과목별 학점 정보 저장
        course_credits = {}
        for _, row in df.iterrows():
            course_name = row['course_name']
            credits = row['credits']
            course_credits[course_name] = credits
            
            # 매핑된 과목명에 대한 학점도 저장
            for old_name, new_name in self.course_name_mapping.items():
                if course_name == old_name:
                    course_credits[new_name] = credits
                elif course_name == new_name:
                    course_credits[old_name] = credits
        
        # 과목 학점 조회 함수
        def get_course_credit(course_name: str) -> int:
            if '학술답사' in course_name:
                return 1
            elif course_name in course_credits:
                return course_credits[course_name]
            else:
                return 3
        def get_display_course_name(course_name: str) -> str:
            for old_name, new_name in self.course_name_mapping.items():
                if course_name == new_name:
                    return f"{new_name}(전 {old_name})"
                elif course_name == old_name:
                    return f"{new_name}(전 {old_name})"
            return course_name
        result = {
            'total_credits': valid_credits,
            'required_courses': {},
            'missing_courses': {},
            'status': '미졸업',
            'details': {}
        }
        context = AnalyzeContext(
            get_display_course_name=get_display_course_name,
            get_course_credit=get_course_credit,
            admission_year=admission_year,
            internship_completed=internship_completed
        )
        # --- 교양 필수 분석 분리 ---
        common_result = self.common_required_analyzer.analyze(df, requirement, student_type, context)
        result['required_courses'].update(common_result['required_courses'])
        result['missing_courses'].update(common_result['missing_courses'])
        result['details'].update(common_result['details'])
        # --- 전공 필수/선택 분석 분리 ---
        major_result = self.major_required_analyzer.analyze(df, requirement, student_type, context)
        result['required_courses'].update(major_result['required_courses'])
        result['missing_courses'].update(major_result['missing_courses'])
        # --- 학술답사 분석 분리 ---
        field_trip_result = self.field_trip_analyzer.analyze(df, requirement, student_type, context)
        result['required_courses'].update(field_trip_result['required_courses'])
        result['missing_courses'].update(field_trip_result['missing_courses'])
        # --- 2025년 요건 분석 분리 ---
        if admission_year >= 2025:
            year2025_result = self.year2025_requirement_analyzer.analyze(df, requirement, student_type, context)
            result['required_courses'].update(year2025_result['required_courses'])
            result['missing_courses'].update(year2025_result['missing_courses'])
        
        # 졸업 가능 여부 판단
        if (result['total_credits'] >= requirement.REQUIREMENTS[student_type]['total_credits'] and
            len(result['missing_courses']) == 0):
            result['status'] = '졸업가능'
        return result