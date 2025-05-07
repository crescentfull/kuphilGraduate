from typing import Any
import pandas as pd
from myapp.services.graduation.context import AnalyzeContext
import logging

logger = logging.getLogger(__name__)

# --- 2025년 요건 분석기 ---
class Year2025RequirementAnalyzer:
    def __init__(self, course_name_mapping):
        self.course_name_mapping = course_name_mapping

    def analyze(self, df: pd.DataFrame, requirement, student_type: str, context: AnalyzeContext):
        logger.info("=== 2025년도 졸업요건 분석 시작 ===")
        logger.info(f"입력 데이터프레임 크기: {df.shape}")
        logger.info(f"전공 기초 과목: {requirement.major_base}")
        logger.info(f"전공 기초 최소 이수 과목 수: {requirement.major_base_min}")
        logger.info(f"전공 선택 과목: {requirement.major_elective}")
        logger.info(f"전공 선택 최소 이수 과목 수: {requirement.major_elective_min}")
        
        result = {
            'required_courses': {},
            'missing_courses': {},
        }
        # 전공 기초 과목 처리
        major_base = requirement.major_base
        major_base_min = requirement.major_base_min
        # 지교로 이수 가능한 과목 리스트
        designated_required = requirement.designated_required
        
        logger.info("전공 기초 과목 확인 중...")
        completed_base = []
        for course in major_base:
            logger.info(f"과목 '{course}' 확인 중...")
            if course in designated_required:
                course_data = df[
                    (df['course_name'] == course) &
                    (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                ]
                actual_category = '전공기초'
                if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                    actual_category = '지교'
                    original_type = '지교(전공기초인정)'
                    logger.info(f"과목 '{course}' 지교로 이수 확인됨")
                else:
                    course_data = df[
                        (df['course_name'] == course) &
                        (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                    ]
                    actual_category = '전공기초'
                    original_type = None
                if not course_data.empty:
                    logger.info(f"과목 '{course}' 이수 확인됨")
                    completed_base.append({
                        'course_name': context.get_display_course_name(course),
                        'category': actual_category,
                        'credits': course_data['credits'].iloc[0],
                        'original_type': original_type or course_data['course_type'].iloc[0]
                    })
                    
                    # 지교로 이수한 전공기초 과목이면 지교 카테고리에도 추가
                    if actual_category == '지교':
                        if '지교' not in result['required_courses']:
                            result['required_courses']['지교'] = []
                        result['required_courses']['지교'].append({
                            'course_name': context.get_display_course_name(course),
                            'category': '지교',
                            'credits': course_data['credits'].iloc[0],
                            'original_type': original_type
                        })
            else:
                logger.warning(f"과목 '{course}' 미이수")
                
        logger.info(f"이수한 전공 기초 과목 수: {len(completed_base)}/{major_base_min}")
        if len(completed_base) >= major_base_min:
            logger.info("전공 기초 과목 요건 충족")
            if '전공기초' not in result['required_courses']:
                result['required_courses']['전공기초'] = []
            result['required_courses']['전공기초'].extend(completed_base)
        else:
            logger.warning(f"전공 기초 과목 요건 미충족: {len(completed_base)}/{major_base_min}")
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
        # 전공 선택 과목 처리
        major_elective = requirement.major_elective
        major_elective_min = requirement.major_elective_min
        designated_required = requirement.designated_required
        
        completed_electives = []
        for course in major_elective:
            if course in designated_required:
                course_data = df[
                    (df['course_name'] == course) &
                    (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필', '지정교양', '지교']))
                ]
                actual_category = '전공선택'
                original_type = None
                if not course_data.empty and course_data['course_type'].iloc[0] in ['지정교양', '지교']:
                    actual_category = '지교'
                    original_type = '지교(전공선택인정)'
            else:
                course_data = df[
                    (df['course_name'] == course) &
                    (df['course_type'].isin(['전공선택', '전선', '전공필수', '전필']))
                ]
                actual_category = '전공선택'
                original_type = None
            if not course_data.empty:
                completed_electives.append({
                    'course_name': context.get_display_course_name(course),
                    'category': actual_category,
                    'credits': course_data['credits'].iloc[0],
                    'original_type': original_type or course_data['course_type'].iloc[0]
                })
                
                # 지교로 이수한 전공선택 과목이면 지교 카테고리에도 추가
                if actual_category == '지교':
                    if '지교' not in result['required_courses']:
                        result['required_courses']['지교'] = []
                    result['required_courses']['지교'].append({
                        'course_name': context.get_display_course_name(course),
                        'category': '지교',
                        'credits': course_data['credits'].iloc[0],
                        'original_type': original_type
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
        # 학술답사 과목 처리
        field_trip = requirement.field_trip or []
        field_trip_min = requirement.field_trip_min
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