from typing import Dict, Any
import pandas as pd
from ...models.graduation_requirement import GraduationRequirementManager
from ..excel.cleaner import clean_dataframe

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
            '핵교': '심교',
            '일교': '일반교양',
            '지교': '지정교양',
            '전선': '전공선택',
            '전필': '전공필수',
            '일선': '일반선택',
            '심교': '심화교양',
        }

    def analyze(self, df: pd.DataFrame, student_type: str, admission_year: int, internship_completed: str = 'no') -> Dict[str, Any]:
        """졸업요건 분석 수행"""
        try:
            # 0. 원본 데이터의 총 학점 합계 확인
            original_total_credits = df['credits'].sum() if 'credits' in df.columns else 0
            print(f"원본 데이터 총 학점: {original_total_credits}")
            
            # 1. 데이터 정제
            df = clean_dataframe(df)
            
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
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'status': '오류',
            }
            
    def _apply_course_name_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """과목명 매핑 적용"""
        # 과목명에서 공백 제거
        df['course_name'] = df['course_name'].str.replace(' ', '')
        
        # 매핑 적용
        for old_name, new_name in self.course_name_mapping.items():
            # 정확한 매칭
            df.loc[df['course_name'] == old_name, 'course_name'] = new_name
            
            # 부분 매칭 (과목명에 old_name이 포함된 경우)
            df.loc[df['course_name'].str.contains(old_name, case=False, na=False), 'course_name'] = new_name
            
        return df
        
    def _apply_course_type_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """과목 구분 매핑 적용"""
        # 과목 구분 매핑
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
            # 학술답사는 1학점
            if '학술답사' in course_name:
                return 1
            # 데이터에서 찾은 학점이 있으면 사용
            elif course_name in course_credits:
                return course_credits[course_name]
            # 기본값 3학점
            else:
                return 3
        
        # 과목명 표시 함수
        def get_display_course_name(course_name: str) -> str:
            # 매핑된 과목인 경우 원래 과목명을 괄호 안에 표시
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
        
        # 공통 필수 과목 체크
        common_required = requirement.REQUIREMENTS[student_type]['common_required']
        for category, courses in common_required.items():
            # 카테고리에 해당하는 과목 구분 결정
            category_types = []
            if category == '기초교양' or category == '기교':
                category_types = ['기초교양', '기교']
            elif category == '핵심교양' or category == '핵교':
                category_types = ['핵심교양', '핵교']
            elif category == '일반교양' or category == '일교':
                category_types = ['일반교양', '일교']
            elif category == '지정교양' or category == '지교':
                category_types = ['지정교양', '지교']
            elif category == '심화교양' or category == '심교':
                category_types = ['심화교양', '심교']
            elif category == '일반선택' or category == '일선':
                category_types = ['일반선택', '일선']
            else:
                category_types = [category]

            # 과목 목록 체크 (courses가 리스트인 경우)
            if isinstance(courses, list):
                for course in courses:
                    # 과목명 매핑
                    course_name = course
                    for old_name, new_name in self.course_name_mapping.items():
                        if old_name == course:
                            course_name = new_name
                            break
                    # 이수한 과목 검색 시 매핑된 이름으로 검색
                    course_data = df[
                        (df['course_name'].str.contains(course, case=False, na=False)) & 
                        (df['course_type'].isin(category_types))
                    ]
                    if not course_data.empty:
                        # 이수
                        if category not in result['required_courses']:
                            result['required_courses'][category] = []
                        result['required_courses'][category].append({
                            'course_name': get_display_course_name(course),
                            'category': category,
                            'credits': course_data['credits'].iloc[0]
                        })
                    else:
                        # 미이수
                        if category not in result['missing_courses']:
                            result['missing_courses'][category] = []
                        result['missing_courses'][category].append({
                            'course_name': get_display_course_name(course),
                            'category': category,
                            'credits': get_course_credit(course)
                        })
            # 수량 요건 체크 (courses가 숫자인 경우, 예: '지교': 5)
            elif isinstance(courses, int):
                # 해당 카테고리의 과목 수 계산
                category_courses = df[df['course_type'].isin(category_types)]
                
                # 해당 카테고리 이수 과목 수
                completed_count = len(category_courses)
                
                # 결과에 추가
                if completed_count >= courses:
                    # 충족한 경우, 이수한 모든 과목을 required_courses에 추가
                    if category not in result['required_courses']:
                        result['required_courses'][category] = []
                    
                    for _, row in category_courses.iterrows():
                        result['required_courses'][category].append({
                            'course_name': get_display_course_name(row['course_name']),
                            'category': category,
                            'credits': row['credits'],
                            'original_type': row['course_type']
                        })
                    
                    # 세부 결과에 추가
                    result['details'][f'{category} 과목 수'] = f'{completed_count}/{courses} (충족)'
                else:
                    # 미충족한 경우, missing_courses에 추가
                    if category not in result['missing_courses']:
                        result['missing_courses'][category] = []
                    
                    # 부족한 과목 수 표시
                    missing_count = courses - completed_count
                    result['missing_courses'][category].append({
                        'course_name': f'{category} 과목 {missing_count}개 더 필요',
                        'category': category,
                        'credits': missing_count * get_course_credit(category)
                    })
                    
                    # 이수한 과목들은 required_courses에 추가
                    if completed_count > 0:
                        if category not in result['required_courses']:
                            result['required_courses'][category] = []
                        
                        for _, row in category_courses.iterrows():
                            result['required_courses'][category].append({
                                'course_name': get_display_course_name(row['course_name']),
                                'category': category,
                                'credits': row['credits'],
                                'original_type': row['course_type']
                            })
                    
                    # 세부 결과에 추가
                    result['details'][f'{category} 과목 수'] = f'{completed_count}/{courses} (미충족)'

        # 전공 과목 체크 (2024년 요건)
        if 'major_required' in requirement.REQUIREMENTS[student_type]:
            # 전공 필수 과목 체크
            major_required = requirement.REQUIREMENTS[student_type]['major_required']
            
            # 지정교양(지교)으로 이수해도 전공 필수로 인정되는 과목들
            major_required_as_designated = [
                '철학의문제들',
                '동양사상과현실문제',
                '논리학'
            ]
            
            for course in major_required:
                # 지정교양으로 이수해도 인정되는 전공 필수 과목인 경우
                if course in major_required_as_designated:
                    course_data = df[
                        (df['course_name'].str.contains(course, case=False, na=False)) & 
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                    ]
                    
                    # 실제 이수구분 확인
                    actual_category = '전공'
                    if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                        actual_category = '지교(전공인정)'
                else:
                    # 일반적인 전공 과목 체크
                    course_data = df[
                        (df['course_name'].str.contains(course, case=False, na=False)) & 
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    actual_category = '전공'
                
                if not course_data.empty:
                    if actual_category not in result['required_courses']:
                        result['required_courses'][actual_category] = []
                    result['required_courses'][actual_category].append({
                        'course_name': get_display_course_name(course),
                        'category': actual_category,
                        'credits': course_data['credits'].iloc[0],
                        'original_type': course_data['course_type'].iloc[0]
                    })
                else:
                    if actual_category not in result['missing_courses']:
                        result['missing_courses'][actual_category] = []
                    result['missing_courses'][actual_category].append({
                        'course_name': get_display_course_name(course),
                        'category': actual_category,
                        'credits': get_course_credit(course)
                    })
            
            # 전공 선택 필수 과목 체크 (2024년 요건)
            if 'major_elective_required' in requirement.REQUIREMENTS[student_type]:
                major_elective_required = requirement.REQUIREMENTS[student_type]['major_elective_required']
                major_elective_min = requirement.REQUIREMENTS[student_type]['major_elective_min']
                
                # 지정교양(지교)으로 이수해도 전공선택으로 인정되는 과목들
                major_elective_as_designated = [
                    '윤리학',
                    '인식론',
                    '한국철학의이해'
                ]
                
                completed_electives = []
                for course in major_elective_required:
                    # 지정교양으로 이수해도 인정되는 전공선택 과목인 경우
                    if course in major_elective_as_designated:
                        course_data = df[
                            (df['course_name'].str.contains(course, case=False, na=False)) & 
                            (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                        ]
                        
                        # 실제 이수구분 확인
                        actual_category = '전공선택'
                        if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                            actual_category = '지교(전공선택인정)'
                    else:
                        # 일반적인 전공선택 과목 체크
                        course_data = df[
                            (df['course_name'].str.contains(course, case=False, na=False)) & 
                            (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                        ]
                        actual_category = '전공선택'
                    
                    if not course_data.empty:
                        completed_electives.append({
                            'course_name': get_display_course_name(course),
                            'category': actual_category,
                            'credits': course_data['credits'].iloc[0],
                            'original_type': course_data['course_type'].iloc[0]
                        })
                
                # 전공 선택 필수 과목 이수 여부 판단
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
                        'credits': missing_count * get_course_credit('전공선택')
                    })
                    
                    # 이수한 과목들은 required_courses에 추가
                    if completed_electives:
                        if '전공선택' not in result['required_courses']:
                            result['required_courses']['전공선택'] = []
                        result['required_courses']['전공선택'].extend(completed_electives)
            
            # 학술답사 체크 (2024년 요건)
            if 'field_trip' in requirement.REQUIREMENTS[student_type] and requirement.REQUIREMENTS[student_type]['field_trip']:
                field_trip = requirement.REQUIREMENTS[student_type]['field_trip']
                field_trip_min = requirement.REQUIREMENTS[student_type]['field_trip_min']
                
                completed_field_trips = []
                for course in field_trip:
                    # 과목명 매핑 적용
                    course_name = course
                    for old_name, new_name in self.course_name_mapping.items():
                        if old_name == course:
                            course_name = new_name
                            break
                    
                    # 정확한 과목명 매칭 사용
                    course_data = df[
                        (df['course_name'] == course_name) & 
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    
                    if not course_data.empty:
                        completed_field_trips.append({
                            'course_name': get_display_course_name(course),
                            'category': '학술답사',
                            'credits': course_data['credits'].iloc[0]
                        })
                
                # 학술답사 이수 여부 판단
                if len(completed_field_trips) >= field_trip_min:
                    if '학술답사' not in result['required_courses']:
                        result['required_courses']['학술답사'] = []
                    result['required_courses']['학술답사'].extend(completed_field_trips)
                else:
                    # 2024학번의 경우, 학술답사 1개 + 인턴십으로도 충족 가능
                    if (admission_year <= 2024 and 
                        len(completed_field_trips) == 1 and 
                        result.get('internship_completed', False)):
                        print(f"학술답사 1개 + 인턴십으로 요건 충족")
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
                                'credits': missing_count * get_course_credit('학술답사')
                            })
                            
                            # 이수한 과목들은 required_courses에 추가
                            if completed_field_trips:
                                if '학술답사' not in result['required_courses']:
                                    result['required_courses']['학술답사'] = []
                                result['required_courses']['학술답사'].extend(completed_field_trips)
        
        # 2025년 요건 처리
        if admission_year >= 2025 and 'major_base' in requirement.REQUIREMENTS[student_type]:
            # 전공기초 과목 체크
            major_base = requirement.REQUIREMENTS[student_type]['major_base']
            major_base_min = requirement.REQUIREMENTS[student_type]['major_base_min']
            
            # 지정교양(지교)으로 이수해도 전공기초로 인정되는 과목들
            major_base_as_designated = [
                '철학의문제들',
                '동양사상과현실문제',
                '논리학'
            ]
            
            completed_base = []
            for course in major_base:
                # 지정교양으로 이수해도 인정되는 전공기초 과목인 경우
                if course in major_base_as_designated:
                    course_data = df[
                        (df['course_name'] == course) & 
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                    ]
                    
                    # 실제 이수구분 확인
                    actual_category = '전공기초'
                    if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                        actual_category = '지교(전공기초인정)'
                else:
                    # 일반적인 전공 과목 체크
                    course_data = df[
                        (df['course_name'] == course) & 
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    actual_category = '전공기초'
                
                if not course_data.empty:
                    completed_base.append({
                        'course_name': get_display_course_name(course),
                        'category': actual_category,
                        'credits': course_data['credits'].iloc[0],
                        'original_type': course_data['course_type'].iloc[0]
                    })
            
            # 전공기초 이수 여부 판단
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
                    'credits': missing_count * get_course_credit('전공기초')
                })
                
                # 이수한 과목들은 required_courses에 추가
                if completed_base:
                    if '전공기초' not in result['required_courses']:
                        result['required_courses']['전공기초'] = []
                    result['required_courses']['전공기초'].extend(completed_base)
            
            # 전공선택 과목 체크 (2025년 요건)
            if 'major_elective' in requirement.REQUIREMENTS[student_type]:
                major_elective = requirement.REQUIREMENTS[student_type]['major_elective']
                major_elective_min = requirement.REQUIREMENTS[student_type]['major_elective_min']
                
                # 지정교양(지교)으로 이수해도 전공선택으로 인정되는 과목들
                major_elective_as_designated = [
                    '윤리학',
                    '인식론',
                    '한국철학의이해'
                ]
                
                completed_electives = []
                for course in major_elective:
                    # 지정교양으로 이수해도 인정되는 전공선택 과목인 경우
                    if course in major_elective_as_designated:
                        course_data = df[
                            (df['course_name'] == course) & 
                            (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                        ]
                        
                        # 실제 이수구분 확인
                        actual_category = '전공선택'
                        if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                            actual_category = '지교(전공선택인정)'
                    else:
                        # 일반적인 전공선택 과목 체크
                        course_data = df[
                            (df['course_name'] == course) & 
                            (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                        ]
                        actual_category = '전공선택'
                    
                    if not course_data.empty:
                        completed_electives.append({
                            'course_name': get_display_course_name(course),
                            'category': actual_category,
                            'credits': course_data['credits'].iloc[0],
                            'original_type': course_data['course_type'].iloc[0]
                        })
                
                # 전공선택 이수 여부 판단
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
                        'credits': missing_count * get_course_credit('전공선택')
                    })
                    
                    # 이수한 과목들은 required_courses에 추가
                    if completed_electives:
                        if '전공선택' not in result['required_courses']:
                            result['required_courses']['전공선택'] = []
                        result['required_courses']['전공선택'].extend(completed_electives)
            
            # 학술답사 체크 (2025년 요건)
            if 'field_trip' in requirement.REQUIREMENTS[student_type] and requirement.REQUIREMENTS[student_type]['field_trip']:
                field_trip = requirement.REQUIREMENTS[student_type]['field_trip']
                field_trip_min = requirement.REQUIREMENTS[student_type]['field_trip_min']
                
                completed_field_trips = []
                for course in field_trip:
                    # 정확한 과목명 매칭 사용
                    course_data = df[
                        (df['course_name'] == course) & 
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    if not course_data.empty:
                        completed_field_trips.append({
                            'course_name': get_display_course_name(course),
                            'category': '학술답사',
                            'credits': course_data['credits'].iloc[0]
                        })
                
                # 학술답사 이수 여부 판단
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
                            'credits': missing_count * get_course_credit('학술답사')
                        })
                        
                        # 이수한 과목들은 required_courses에 추가
                        if completed_field_trips:
                            if '학술답사' not in result['required_courses']:
                                result['required_courses']['학술답사'] = []
                            result['required_courses']['학술답사'].extend(completed_field_trips)

        # 졸업 가능 여부 판단
        if (result['total_credits'] >= requirement.REQUIREMENTS[student_type]['total_credits'] and
            len(result['missing_courses']) == 0):
            result['status'] = '졸업가능'

        return result