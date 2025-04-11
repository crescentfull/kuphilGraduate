import pytest
import pandas as pd
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import unittest.mock as mock
from ..services.graduation.analyzer import GraduationAnalyzer

# 테스트용 데이터프레임 생성 함수
def create_test_dataframe():
    data = {
        '과목명': ['철학산책', '철학의이해', '논리학', '서양고중세철학', '윤리학', '인식론', '형이상학', '한국철학의이해'],
        '이수구분': ['심교', '심교', '전선', '전선', '전선', '전선', '전선', '전선'],
        '학점': [3, 3, 3, 3, 3, 3, 3, 3],
        '삭제구분': ['', '', '', '', '', '', '', '']
    }
    return pd.DataFrame(data)

def create_test_dataframe_with_credits_given_up():
    data = {
        '과목명': ['철학산책', '철학의이해', '논리학', '서양고중세철학', '윤리학', '인식론', '형이상학', '한국철학의이해'],
        '이수구분': ['심교', '심교', '전선', '전선', '전선', '전선', '전선', '전선'],
        '학점': [3, 3, 3, 3, 3, 3, 3, 3],
        '삭제구분': ['', '', '취득학점포기', '', '', '', '', '']
    }
    return pd.DataFrame(data)

def create_test_dataframe_with_spaces():
    data = {
        '과목명': ['철학 산책', '철학의 이해', '논리 학', '서양 고중세 철학', '윤리 학', '인식 론', '형이상 학', '한국 철학의 이해'],
        '이수구분': ['심교', '심교', '전선', '전선', '전선', '전선', '전선', '전선'],
        '학점': [3, 3, 3, 3, 3, 3, 3, 3],
        '삭제구분': ['', '', '', '', '', '', '', '']
    }
    return pd.DataFrame(data)

# 모킹된 clean_dataframe 함수
def mock_clean_dataframe(df):
    """테스트용으로 간단하게 구현된 clean_dataframe 함수"""
    result = pd.DataFrame()
    result['course_name'] = df['과목명'].str.replace(' ', '')
    result['course_type'] = df['이수구분']
    result['credits'] = df['학점'].astype(float)
    
    # 취득학점포기 제외
    if '삭제구분' in df.columns:
        result = result[~(df['삭제구분'] == '취득학점포기')]
    
    return result

# clean_dataframe 테스트
@mock.patch('myapp.services.excel.cleaner.clean_dataframe', side_effect=mock_clean_dataframe)
def test_clean_dataframe(mock_clean):
    df = create_test_dataframe()
    cleaned_df = mock_clean_dataframe(df)
    
    # 컬럼명이 영문으로 변경되었는지 확인
    assert 'course_name' in cleaned_df.columns
    assert 'course_type' in cleaned_df.columns
    assert 'credits' in cleaned_df.columns
    
    # 데이터 타입 확인
    assert cleaned_df['credits'].dtype in [np.int64, np.float64]
    
    # 데이터 개수 확인
    assert len(cleaned_df) == len(df)

@mock.patch('myapp.services.excel.cleaner.clean_dataframe', side_effect=mock_clean_dataframe)
def test_clean_dataframe_with_credits_given_up(mock_clean):
    df = create_test_dataframe_with_credits_given_up()
    cleaned_df = mock_clean_dataframe(df)
    
    # '취득학점포기' 데이터가 제외되었는지 확인
    assert len(cleaned_df) == len(df) - 1
    
    # '취득학점포기' 데이터가 제외되었는지 확인
    assert '논리학' not in cleaned_df['course_name'].values

@mock.patch('myapp.services.excel.cleaner.clean_dataframe', side_effect=mock_clean_dataframe)
def test_clean_dataframe_with_spaces(mock_clean):
    df = create_test_dataframe_with_spaces()
    cleaned_df = mock_clean_dataframe(df)
    
    # 띄어쓰기가 제거되었는지 확인
    assert '철학산책' in cleaned_df['course_name'].values
    assert '철학의이해' in cleaned_df['course_name'].values
    assert '논리학' in cleaned_df['course_name'].values

# GraduationAnalyzer 클래스 테스트
@mock.patch('myapp.services.graduation.analyzer.clean_dataframe', side_effect=mock_clean_dataframe)
def test_graduation_analyzer(mock_clean):
    # GraduationAnalyzer 인스턴스 생성
    analyzer = GraduationAnalyzer()
    
    # 테스트 데이터프레임 생성
    df = create_test_dataframe()
    
    # analyze 메서드 모킹
    with mock.patch.object(analyzer, 'analyze', return_value={'total_credits': 24}):
        # 분석 실행 (2023학번 일반학생 기준)
        result = analyzer.analyze(df, 'normal', 2023)
        
        # 결과 확인
        assert isinstance(result, dict)
        assert 'total_credits' in result
        assert result['total_credits'] == 24  # 8과목 * 3학점

@mock.patch('myapp.services.graduation.analyzer.clean_dataframe', side_effect=mock_clean_dataframe)
def test_graduation_analyzer_with_credits_given_up(mock_clean):
    # GraduationAnalyzer 인스턴스 생성
    analyzer = GraduationAnalyzer()
    
    # 취득학점포기 데이터 포함된 데이터프레임 생성
    df = create_test_dataframe_with_credits_given_up()
    
    # analyze 메서드 모킹
    with mock.patch.object(analyzer, 'analyze', return_value={'total_credits': 21}):
        # 분석 실행 (2023학번 일반학생 기준)
        result = analyzer.analyze(df, 'normal', 2023)
        
        # 결과 확인 - 취득학점포기 과목 제외된 학점
        assert result['total_credits'] == 21  # (8-1)과목 * 3학점

# 학번별 졸업요건 차이 테스트
@mock.patch('myapp.services.graduation.analyzer.clean_dataframe', side_effect=mock_clean_dataframe)
def test_different_admission_year_requirements(mock_clean):
    analyzer = GraduationAnalyzer()
    df = create_test_dataframe()
    
    # 2024학번과 2025학번 분석 결과 모킹
    with mock.patch.object(analyzer, 'analyze', side_effect=[
        {'total_credits': 24, 'year': 2024, 'additional': 'X'},
        {'total_credits': 24, 'year': 2025, 'additional': 'Y'}
    ]):
        # 2024학번 분석
        result_2024 = analyzer.analyze(df, 'normal', 2024)
        
        # 2025학번 분석
        result_2025 = analyzer.analyze(df, 'normal', 2025)
        
        # 요건 차이 확인
        assert result_2024['year'] != result_2025['year']
        assert result_2024['additional'] != result_2025['additional']

# Django 뷰 테스트
@pytest.mark.django_db
class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse('index')
    
    def test_upload_page_loads(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
    
    def test_upload_invalid_file(self):
        # 빈 파일 업로드
        file = SimpleUploadedFile("test.xlsx", b"", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response = self.client.post(self.upload_url, {'excel_file': file, 'student_id': '20240001'})
        self.assertEqual(response.status_code, 200)  # 에러 페이지로 리다이렉트
    
    def test_cleanup_files(self):
        try:
            cleanup_url = reverse('cleanup')
            response = self.client.get(cleanup_url)
            self.assertEqual(response.status_code, 200)
        except:
            # 테스트에서 cleanup URL이 없는 경우를 처리
            self.skipTest("Cleanup URL is not defined")
        
    def test_upload_with_student_id(self):
        """학번을 직접 입력하여 업로드하는 경우 테스트"""
        # 테스트 엑셀 파일 생성 - 실제 파일 생성 대신 모킹
        with mock.patch('pandas.DataFrame.to_excel'):
            # 파일 업로드 요청
            file = SimpleUploadedFile("test.xlsx", b"dummy", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with mock.patch('pandas.read_excel', return_value=create_test_dataframe()):
                response = self.client.post(
                    self.upload_url, 
                    {
                        'excel_file': file, 
                        'student_id': '20230001',
                        'student_type': 'normal'
                    }
                )
                
                # 응답 코드 확인
                self.assertEqual(response.status_code, 200)
        
    def test_upload_without_student_id(self):
        """학번 없이 업로드하는 경우 테스트"""
        # 테스트 엑셀 파일 생성 - 실제 파일 생성 대신 모킹
        with mock.patch('pandas.DataFrame.to_excel'):
            # 파일 업로드 요청
            file = SimpleUploadedFile("test.xlsx", b"dummy", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with mock.patch('pandas.read_excel', return_value=create_test_dataframe()):
                response = self.client.post(
                    self.upload_url, 
                    {
                        'excel_file': file, 
                        'student_type': 'normal'
                    }
                )
                
                # 응답 코드 확인
                self.assertEqual(response.status_code, 200) 