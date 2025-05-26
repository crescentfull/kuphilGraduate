import pytest
import pandas as pd
from django.test import Client
from django.contrib.auth.models import User


@pytest.fixture
def client():
    """Django 테스트 클라이언트 픽스처"""
    return Client()


@pytest.fixture
def sample_dataframe():
    """테스트용 샘플 데이터프레임"""
    data = {
        'course_name': ['철학산책', '철학의이해', '논리학', '서양고중세철학', '윤리학'],
        'course_type': ['심교', '심교', '전선', '전선', '전선'],
        'credits': [3, 3, 3, 3, 3],
        'grade': ['A+', 'A', 'B+', 'B', 'A'],
        'year': [2023, 2023, 2023, 2024, 2024],
        'semester': [1, 2, 1, 2, 1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataframe_with_f_grade():
    """F학점이 포함된 테스트용 데이터프레임"""
    data = {
        'course_name': ['철학산책', '철학의이해', '논리학', '서양고중세철학', '윤리학'],
        'course_type': ['심교', '심교', '전선', '전선', '전선'],
        'credits': [3, 3, 3, 3, 3],
        'grade': ['A+', 'F', 'B+', 'N', 'A'],
        'year': [2023, 2023, 2023, 2024, 2024],
        'semester': [1, 2, 1, 2, 1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_excel_file_content():
    """테스트용 엑셀 파일 내용"""
    return b"dummy excel content" 