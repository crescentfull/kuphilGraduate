import pytest
import pandas as pd
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
import tempfile
from ..views import (
    clean_dataframe,
    analyze_completed_courses,
    get_graduation_requirements,
    analyze_graduation_requirements
)

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

# clean_dataframe 함수 테스트
def test_clean_dataframe():
    df = create_test_dataframe()
    cleaned_df = clean_dataframe(df)
    
    # 컬럼명이 영문으로 변경되었는지 확인
    assert 'course_name' in cleaned_df.columns
    assert 'course_type' in cleaned_df.columns
    assert 'credits' in cleaned_df.columns
    
    # 데이터 타입 확인
    assert cleaned_df['credits'].dtype in [np.int64, np.float64]
    
    # 데이터 개수 확인
    assert len(cleaned_df) == len(df)

def test_clean_dataframe_with_credits_given_up():
    df = create_test_dataframe_with_credits_given_up()
    cleaned_df = clean_dataframe(df)
    
    # '취득학점포기' 데이터가 제외되었는지 확인
    assert len(cleaned_df) == len(df) - 1
    
    # '취득학점포기' 데이터가 제외되었는지 확인
    assert '논리학' not in cleaned_df['course_name'].values

def test_clean_dataframe_with_spaces():
    df = create_test_dataframe_with_spaces()
    cleaned_df = clean_dataframe(df)
    
    # 띄어쓰기가 제거되었는지 확인
    assert '철학산책' in cleaned_df['course_name'].values
    assert '철학의이해' in cleaned_df['course_name'].values
    assert '논리학' in cleaned_df['course_name'].values

# analyze_completed_courses 함수 테스트
def test_analyze_completed_courses():
    df = create_test_dataframe()
    df = clean_dataframe(df)
    completed_courses = analyze_completed_courses(df)
    
    # 반환된 딕셔너리의 키가 과목명인지 확인
    assert '철학산책' in completed_courses
    assert '철학의이해' in completed_courses
    
    # 반환된 딕셔너리의 값이 올바른 형식인지 확인
    assert 'course_name' in completed_courses['철학산책']
    assert 'category' in completed_courses['철학산책']
    assert 'credits' in completed_courses['철학산책']
    
    # 값이 올바른지 확인
    assert completed_courses['철학산책']['category'] == '심교'
    assert completed_courses['철학산책']['credits'] == 3

# get_graduation_requirements 함수 테스트
def test_get_graduation_requirements():
    # 일반학생 졸업요건 확인
    normal_requirements = get_graduation_requirements('normal')
    assert 'common_required' in normal_requirements
    assert '전선' in normal_requirements
    assert '전선_min' in normal_requirements
    assert 'internship_required' in normal_requirements
    
    # 편입생 졸업요건 확인
    transfer_requirements = get_graduation_requirements('transfer')
    assert '전선' in transfer_requirements
    assert '전선_min' in transfer_requirements
    
    # 다전공자 졸업요건 확인
    double_requirements = get_graduation_requirements('double')
    assert 'common_required' in double_requirements
    assert '전선' in double_requirements
    assert '전선_min' in double_requirements
    
    # 부전공자 졸업요건 확인
    minor_requirements = get_graduation_requirements('minor')
    assert '전선' in minor_requirements
    assert '전선_min' in minor_requirements

# analyze_graduation_requirements 함수 테스트
def test_analyze_graduation_requirements_normal():
    df = create_test_dataframe()
    df = clean_dataframe(df)
    result = analyze_graduation_requirements(df, 'normal')
    
    # 결과 형식 확인
    assert 'total_credits' in result
    assert 'required_courses' in result
    assert 'missing_courses' in result
    assert 'status' in result
    assert 'details' in result
    
    # 총 이수학점 확인
    assert result['total_credits'] == 24  # 8과목 * 3학점
    
    # 이수한 필수 과목 확인
    assert '심교' in result['required_courses']
    assert len(result['required_courses']['심교']) == 2  # 철학산책, 철학의이해
    
    # 미이수 필수 과목 확인
    assert '지교' in result['missing_courses']
    
    # 전선 과목 확인
    assert '전선' in result['required_courses']
    assert len(result['required_courses']['전선']) == 6  # 6개 전선 과목
    
    # 세부 요건 확인
    assert '전선' in result['details']
    
    # 졸업 가능 여부 확인
    assert result['status'] == '미졸업'  # 총 이수학점이 130학점 미만이므로 미졸업

def test_analyze_graduation_requirements_with_credits_given_up():
    df = create_test_dataframe_with_credits_given_up()
    df = clean_dataframe(df)
    result = analyze_graduation_requirements(df, 'normal')
    
    # 총 이수학점 확인 (취득학점포기 과목 제외)
    assert result['total_credits'] == 21  # 7과목 * 3학점
    
    # 전선 과목 확인 (취득학점포기 과목 제외)
    assert '전선' in result['required_courses']
    assert len(result['required_courses']['전선']) == 5  # 5개 전선 과목

# Django 뷰 테스트
@pytest.mark.django_db
class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.upload_url = reverse('upload')
    
    def test_upload_page_loads(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
    
    def test_upload_invalid_file(self):
        # 빈 파일 업로드
        file = SimpleUploadedFile("test.xlsx", b"", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response = self.client.post(self.upload_url, {'excel_file': file, 'student_type': 'normal'})
        self.assertEqual(response.status_code, 200)  # 에러 페이지로 리다이렉트
    
    def test_cleanup_files(self):
        response = self.client.get(reverse('cleanup'))
        self.assertEqual(response.status_code, 200) 