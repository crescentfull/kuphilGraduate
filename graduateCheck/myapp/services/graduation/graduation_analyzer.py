import pandas as pd
from typing import Dict, Any
from myapp.services.cleaner import clean_dataframe
from myapp.services.graduation.context import AnalyzeContext
from myapp.services.graduation.common_required import CommonRequiredAnalyzer
from myapp.services.graduation.major_required import MajorRequiredAnalyzer
from myapp.services.graduation.field_trip import FieldTripAnalyzer
from myapp.services.graduation.year2025 import Year2025RequirementAnalyzer
from myapp.models.graduation_requirement import GraduationRequirementManager
import logging

logger = logging.getLogger(__name__)

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

    def analyze(self, df: pd.DataFrame, student_type: str, admission_year: int, internship_completed: str = 'no'):
        """졸업요건 분석 수행"""
        try:
            # 0. 원본 데이터의 총 학점 합계 확인
            original_total_credits = df['credits'].sum() if 'credits' in df.columns else 0
            logger.info(f"원본 데이터 총 학점: {original_total_credits}")
            
            # 1. 데이터 정제
            df = clean_dataframe(df)
            
            # F/N 학점 과목 추출
            f_grade_courses = []
            # F/N 학점 과목 수 디버그 로깅
            count_F = len(df[df['grade'] == 'F'])
            count_N = len(df[df['grade'] == 'N'])
            logger.info(f"F학점 과목 수: {count_F}, N학점 과목 수: {count_N}")
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
            logger.debug(f"정제 후 총 학점: {cleaned_total_credits}")
            # 2. 과목명 매핑 적용
            df = self._apply_course_name_mapping(df)
            # 3. 과목 구분 매핑 적용
            df = self._apply_course_type_mapping(df)
            
            # 3.5 매핑 후 총 학점 확인
            mapped_total_credits = df['credits'].sum()
            logger.debug(f"매핑 후 총 학점: {mapped_total_credits}")
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
            logger.info(f"인턴십 이수 여부: {result['internship_completed']}")
            
            # 8. 인턴십이 필수인 경우(2017학번~2024학번) 이수 여부 확인
            if requirement.internship_required and (2017 <= admission_year <= 2020) and not result['internship_completed']:
                result['status'] = '미달'
                result.setdefault('missing_requirements', []).append('인턴십 미이수')
            result['f_grade_courses'] = f_grade_courses
            return result
        except Exception as e:
            return {
                'error': str(e),
                'status': '오류',
            }

    def _apply_course_name_mapping(self, df: pd.DataFrame):
        df['course_name'] = df['course_name'].str.replace(' ', '')
        
        # 매핑 적용
        for old_name, new_name in self.course_name_mapping.items():
            df.loc[df['course_name'] == old_name, 'course_name'] = new_name
        return df

    def _apply_course_type_mapping(self, df: pd.DataFrame):
        for old_type, new_type in self.course_type_mapping.items():
            df.loc[df['course_type'] == old_type, 'course_type'] = new_type
        return df

    def _analyze_requirements(self, df: pd.DataFrame, requirement: Any, student_type: str, admission_year: int, internship_completed: str = 'no'):
        """졸업요건 상세 분석"""
        valid_credits = df[
            (df['grade'].notna()) & 
            (~df['grade'].isin(['F', 'N']))
        ]['credits'].sum() if 'grade' in df.columns else df['credits'].sum()
        logger.info(f"유효한 총 이수학점: {valid_credits}")
        
        course_credits = {}
        for _, row in df.iterrows():
            course_name = row['course_name']
            credits = row['credits']
            course_credits[course_name] = credits
            for old_name, new_name in self.course_name_mapping.items():
                if course_name == old_name:
                    course_credits[new_name] = credits
                elif course_name == new_name:
                    course_credits[old_name] = credits

        def get_course_credit(course_name: str):
            if '학술답사' in course_name:
                return 1
            elif course_name in course_credits:
                return course_credits[course_name]
            else:
                return 3

        def get_display_course_name(course_name: str):
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
        common_result = self.common_required_analyzer.analyze(df, requirement, student_type, context)
        result['required_courses'].update(common_result['required_courses'])
        result['missing_courses'].update(common_result['missing_courses'])
        result['details'].update(common_result['details'])

        major_result = self.major_required_analyzer.analyze(df, requirement, student_type, context)
        result['required_courses'].update(major_result['required_courses'])
        result['missing_courses'].update(major_result['missing_courses'])
        result['details'].update(major_result['details'])

        field_trip_result = self.field_trip_analyzer.analyze(df, requirement, student_type, context)
        result['required_courses'].update(field_trip_result['required_courses'])
        result['missing_courses'].update(field_trip_result['missing_courses'])

        if admission_year >= 2025:
            year2025_result = self.year2025_requirement_analyzer.analyze(df, requirement, student_type, context)
            result['required_courses'].update(year2025_result['required_courses'])
            result['missing_courses'].update(year2025_result['missing_courses'])

        # 졸업 가능 여부 판단
        if result['total_credits'] >= requirement.total_credits and len(result['missing_courses']) == 0:
            result['status'] = '졸업가능'
        return result 