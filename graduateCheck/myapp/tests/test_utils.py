import pytest
import pandas as pd
from unittest.mock import patch, Mock
import tempfile
import os


class TestDataFrameUtils:
    """데이터프레임 관련 유틸리티 테스트"""
    
    def test_create_sample_dataframe(self):
        """샘플 데이터프레임 생성 테스트"""
        data = {
            'course_name': ['철학산책', '논리학', '윤리학'],
            'course_type': ['심교', '전선', '전선'],
            'credits': [3, 3, 3],
            'grade': ['A', 'B+', 'A'],
            'year': [2024, 2024, 2024],
            'semester': [1, 1, 2]
        }
        df = pd.DataFrame(data)
        
        assert len(df) == 3
        assert 'course_name' in df.columns
        assert 'course_type' in df.columns
        assert 'credits' in df.columns
        assert df['credits'].sum() == 9
    
    def test_dataframe_filtering(self):
        """데이터프레임 필터링 테스트"""
        data = {
            'course_name': ['철학산책', '논리학', '윤리학', '인식론'],
            'course_type': ['심교', '전선', '전선', '전선'],
            'credits': [3, 3, 3, 3],
            'grade': ['A', 'F', 'B+', 'N']
        }
        df = pd.DataFrame(data)
        
        # F, N 학점 제외 필터링
        valid_df = df[~df['grade'].isin(['F', 'N'])]
        
        assert len(valid_df) == 2
        assert '논리학' not in valid_df['course_name'].values
        assert '인식론' not in valid_df['course_name'].values
        assert '철학산책' in valid_df['course_name'].values
        assert '윤리학' in valid_df['course_name'].values
    
    def test_dataframe_grouping(self):
        """데이터프레임 그룹핑 테스트"""
        data = {
            'course_name': ['철학산책', '철학의이해', '논리학', '윤리학'],
            'course_type': ['심교', '심교', '전선', '전선'],
            'credits': [3, 3, 3, 3]
        }
        df = pd.DataFrame(data)
        
        # 과목 구분별 그룹핑
        grouped = df.groupby('course_type')['credits'].sum()
        
        assert grouped['심교'] == 6
        assert grouped['전선'] == 6
    
    def test_dataframe_validation(self):
        """데이터프레임 유효성 검사 테스트"""
        # 필수 컬럼이 있는 경우
        valid_data = {
            'course_name': ['철학산책'],
            'course_type': ['심교'],
            'credits': [3]
        }
        valid_df = pd.DataFrame(valid_data)
        
        required_columns = ['course_name', 'course_type', 'credits']
        assert all(col in valid_df.columns for col in required_columns)
        
        # 필수 컬럼이 없는 경우
        invalid_data = {
            'course_name': ['철학산책'],
            'credits': [3]
            # course_type 누락
        }
        invalid_df = pd.DataFrame(invalid_data)
        
        assert not all(col in invalid_df.columns for col in required_columns)


class TestFileUtils:
    """파일 관련 유틸리티 테스트"""
    
    def test_create_temp_excel_file(self):
        """임시 엑셀 파일 생성 테스트"""
        data = {
            'course_name': ['철학산책', '논리학'],
            'course_type': ['심교', '전선'],
            'credits': [3, 3]
        }
        df = pd.DataFrame(data)
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        # 파일이 생성되었는지 확인
        assert os.path.exists(tmp_file_path)
        
        # 파일 내용 확인
        read_df = pd.read_excel(tmp_file_path)
        assert len(read_df) == 2
        assert 'course_name' in read_df.columns
        
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
        assert not os.path.exists(tmp_file_path)
    
    def test_file_content_reading(self):
        """파일 내용 읽기 테스트"""
        data = {
            'course_name': ['철학산책'],
            'course_type': ['심교'],
            'credits': [3]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        # 파일 내용을 바이트로 읽기
        with open(tmp_file_path, 'rb') as f:
            file_content = f.read()
        
        assert isinstance(file_content, bytes)
        assert len(file_content) > 0
        
        # 정리
        os.unlink(tmp_file_path)


class TestStringUtils:
    """문자열 관련 유틸리티 테스트"""
    
    def test_course_name_normalization(self):
        """과목명 정규화 테스트"""
        test_cases = [
            ('철학 산책', '철학산책'),
            ('철학의 이해', '철학의이해'),
            ('논리 학', '논리학'),
            ('서양 고중세 철학', '서양고중세철학'),
        ]
        
        for input_name, expected_name in test_cases:
            normalized_name = input_name.replace(' ', '')
            assert normalized_name == expected_name
    
    def test_course_type_mapping(self):
        """과목 구분 매핑 테스트"""
        mapping = {
            '기교': '기초교양',
            '핵교': '핵심교양',
            '일교': '일반교양',
            '지교': '지정교양',
            '전선': '전공선택',
            '전필': '전공필수',
            '심교': '심화교양',
        }
        
        for short_type, full_type in mapping.items():
            assert mapping[short_type] == full_type
    
    def test_student_id_year_extraction(self):
        """학번에서 입학년도 추출 테스트"""
        test_cases = [
            ('20240001', 2024),
            ('20250123', 2025),
            ('20230456', 2023),
            ('20220789', 2022),
        ]
        
        for student_id, expected_year in test_cases:
            extracted_year = int(student_id[:4])
            assert extracted_year == expected_year
    
    def test_grade_validation(self):
        """성적 유효성 검사 테스트"""
        valid_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F', 'P', 'N']
        invalid_grades = ['X', 'Z', '1', '2', 'AA', 'BB']
        
        for grade in valid_grades:
            assert grade in valid_grades
        
        for grade in invalid_grades:
            assert grade not in valid_grades


class TestCalculationUtils:
    """계산 관련 유틸리티 테스트"""
    
    def test_credit_calculation(self):
        """학점 계산 테스트"""
        credits_list = [3, 3, 3, 2, 1]
        total_credits = sum(credits_list)
        
        assert total_credits == 12
    
    def test_gpa_calculation_mock(self):
        """GPA 계산 모킹 테스트"""
        # 실제 GPA 계산 로직이 있다면 해당 함수를 테스트
        # 여기서는 기본적인 구조만 제공
        
        def mock_calculate_gpa(grades, credits):
            """모킹된 GPA 계산 함수"""
            grade_points = {
                'A+': 4.5, 'A': 4.0, 'B+': 3.5, 'B': 3.0,
                'C+': 2.5, 'C': 2.0, 'D+': 1.5, 'D': 1.0, 'F': 0.0
            }
            
            total_points = 0
            total_credits = 0
            
            for grade, credit in zip(grades, credits):
                if grade in grade_points:
                    total_points += grade_points[grade] * credit
                    total_credits += credit
            
            return total_points / total_credits if total_credits > 0 else 0.0
        
        grades = ['A+', 'A', 'B+']
        credits = [3, 3, 3]
        
        gpa = mock_calculate_gpa(grades, credits)
        expected_gpa = (4.5 * 3 + 4.0 * 3 + 3.5 * 3) / 9
        
        assert abs(gpa - expected_gpa) < 0.01
    
    def test_percentage_calculation(self):
        """백분율 계산 테스트"""
        completed = 45
        required = 60
        
        percentage = (completed / required) * 100
        
        assert percentage == 75.0
    
    def test_remaining_credits_calculation(self):
        """남은 학점 계산 테스트"""
        total_required = 130
        completed = 95
        
        remaining = max(0, total_required - completed)
        
        assert remaining == 35
        
        # 이미 졸업 요건을 충족한 경우
        completed_over = 135
        remaining_over = max(0, total_required - completed_over)
        
        assert remaining_over == 0


class TestValidationUtils:
    """유효성 검사 관련 유틸리티 테스트"""
    
    def test_student_id_validation(self):
        """학번 유효성 검사 테스트"""
        valid_student_ids = ['20240001', '20250123', '20230456']
        invalid_student_ids = ['2024001', '202400001', 'abcd0001', '']
        
        def is_valid_student_id(student_id):
            return (
                isinstance(student_id, str) and
                len(student_id) == 8 and
                student_id.isdigit() and
                student_id.startswith(('202', '201'))
            )
        
        for student_id in valid_student_ids:
            assert is_valid_student_id(student_id)
        
        for student_id in invalid_student_ids:
            assert not is_valid_student_id(student_id)
    
    def test_file_extension_validation(self):
        """파일 확장자 유효성 검사 테스트"""
        valid_files = ['grades.xlsx', 'transcript.xls', 'data.XLSX']
        invalid_files = ['grades.txt', 'transcript.pdf', 'data.csv', 'file']
        
        def is_valid_excel_file(filename):
            return filename.lower().endswith(('.xlsx', '.xls'))
        
        for filename in valid_files:
            assert is_valid_excel_file(filename)
        
        for filename in invalid_files:
            assert not is_valid_excel_file(filename)
    
    def test_credit_range_validation(self):
        """학점 범위 유효성 검사 테스트"""
        valid_credits = [1, 2, 3, 4, 5, 6]
        invalid_credits = [0, -1, 7, 10, 0.5]
        
        def is_valid_credit(credit):
            return isinstance(credit, (int, float)) and 1 <= credit <= 6
        
        for credit in valid_credits:
            assert is_valid_credit(credit)
        
        for credit in invalid_credits:
            assert not is_valid_credit(credit) 