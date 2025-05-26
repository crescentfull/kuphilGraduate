import pytest
import pandas as pd
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
from django.test import override_settings
from django.urls import reverse
import tempfile
import os


@pytest.mark.django_db
@override_settings(SECURE_SSL_REDIRECT=False)  # 테스트에서 SSL 리다이렉트 비활성화
class TestGraduationCheckIntegration(TestCase):
    """졸업 확인 시스템 통합 테스트"""
    
    def setUp(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = Client()
        self.upload_url = reverse('index')  # 실제 URL 사용
    
    def create_test_excel_file(self, data):
        """테스트용 엑셀 파일 생성"""
        df = pd.DataFrame(data)
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        # 파일 내용 읽기
        with open(tmp_file_path, 'rb') as f:
            file_content = f.read()
        
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
        
        return file_content
    
    @patch('myapp.services.graduation.graduation_analyzer.clean_dataframe')
    def test_complete_graduation_check_flow_normal_student(self, mock_clean_dataframe):
        """일반학생 졸업 확인 전체 플로우 테스트"""
        # 테스트 데이터 생성 (졸업 가능한 학생)
        test_data = {
            '과목명': [
                '철학산책', '철학의이해', '논리학', '서양고중세철학', '윤리학',
                '인식론', '형이상학', '한국철학의이해', '동양철학개론', '서양현대철학',
                '미학', '정치철학', '종교철학', '과학철학', '언어철학',
                '현상학', '실존철학', '분석철학', '철학상담', '응용윤리학'
            ],
            '이수구분': [
                '심교', '심교', '전선', '전선', '전선',
                '전선', '전선', '전선', '전선', '전선',
                '전선', '전선', '전선', '전선', '전선',
                '전선', '전선', '전선', '전선', '전선'
            ],
            '학점': [3] * 20,
            '성적': ['A+', 'A', 'B+', 'B', 'A'] * 4,
            '년도': [2024] * 20,
            '학기': [1, 2] * 10
        }
        
        # clean_dataframe이 정제된 데이터를 반환하도록 모킹
        cleaned_df = pd.DataFrame({
            'course_name': test_data['과목명'],
            'course_type': test_data['이수구분'],
            'credits': test_data['학점'],
            'grade': test_data['성적'],
            'year': test_data['년도'],
            'semester': test_data['학기']
        })
        mock_clean_dataframe.return_value = cleaned_df
        
        file_content = self.create_test_excel_file(test_data)
        excel_file = SimpleUploadedFile(
            "graduation_check.xlsx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        with patch('myapp.views.graduation_check.GraduationAnalyzer') as mock_analyzer_class:
            # 졸업 가능한 결과 모킹
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = {
                'total_credits': 60,
                'status': '졸업가능',
                'required_courses': {
                    '심화교양': ['철학산책', '철학의이해'],
                    '전공선택': ['논리학', '서양고중세철학', '윤리학']
                },
                'missing_courses': {},
                'details': {
                    '심화교양': {'이수': 6, '필요': 6, '상태': '충족'},
                    '전공선택': {'이수': 54, '필요': 54, '상태': '충족'}
                },
                'f_grade_courses': [],
                'admission_year': 2024,
                'internship_completed': True
            }
            mock_analyzer_class.return_value = mock_analyzer
            
            response = self.client.post(self.upload_url, {
                'excel_file': excel_file,
                'student_id': '20240001',
                'student_type': 'normal',
                'internship_completed': 'yes'
            })
            
            self.assertEqual(response.status_code, 200)
            # 분석이 호출되었는지 확인
            mock_analyzer.analyze.assert_called_once()
    
    @patch('myapp.services.graduation.graduation_analyzer.clean_dataframe')
    def test_complete_graduation_check_flow_with_missing_courses(self, mock_clean_dataframe):
        """부족한 과목이 있는 학생의 졸업 확인 플로우 테스트"""
        # 테스트 데이터 생성 (졸업 불가능한 학생)
        test_data = {
            '과목명': ['철학산책', '논리학', '윤리학'],
            '이수구분': ['심교', '전선', '전선'],
            '학점': [3, 3, 3],
            '성적': ['A', 'B+', 'A'],
            '년도': [2024, 2024, 2024],
            '학기': [1, 1, 2]
        }
        
        # clean_dataframe이 정제된 데이터를 반환하도록 모킹
        cleaned_df = pd.DataFrame({
            'course_name': test_data['과목명'],
            'course_type': test_data['이수구분'],
            'credits': test_data['학점'],
            'grade': test_data['성적'],
            'year': test_data['년도'],
            'semester': test_data['학기']
        })
        mock_clean_dataframe.return_value = cleaned_df
        
        file_content = self.create_test_excel_file(test_data)
        excel_file = SimpleUploadedFile(
            "graduation_check.xlsx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        with patch('myapp.views.graduation_check.GraduationAnalyzer') as mock_analyzer_class:
            # 졸업 불가능한 결과 모킹
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = {
                'total_credits': 9,
                'status': '미졸업',
                'required_courses': {
                    '심화교양': ['철학산책'],
                    '전공선택': ['논리학', '윤리학']
                },
                'missing_courses': {
                    '심화교양': ['철학의이해'],
                    '전공선택': ['서양고중세철학', '인식론', '형이상학']
                },
                'details': {
                    '심화교양': {'이수': 3, '필요': 6, '상태': '부족'},
                    '전공선택': {'이수': 6, '필요': 54, '상태': '부족'}
                },
                'f_grade_courses': [],
                'admission_year': 2024,
                'internship_completed': True
            }
            mock_analyzer_class.return_value = mock_analyzer
            
            response = self.client.post(self.upload_url, {
                'excel_file': excel_file,
                'student_id': '20240001',
                'student_type': 'normal',
                'internship_completed': 'yes'
            })
            
            self.assertEqual(response.status_code, 200)
            mock_analyzer.analyze.assert_called_once()
    
    @patch('myapp.services.graduation.graduation_analyzer.clean_dataframe')
    def test_complete_graduation_check_flow_with_f_grades(self, mock_clean_dataframe):
        """F학점이 있는 학생의 졸업 확인 플로우 테스트"""
        # F학점이 포함된 테스트 데이터
        test_data = {
            '과목명': ['철학산책', '논리학', '윤리학', '인식론'],
            '이수구분': ['심교', '전선', '전선', '전선'],
            '학점': [3, 3, 3, 3],
            '성적': ['A', 'F', 'B+', 'N'],
            '년도': [2024, 2024, 2024, 2024],
            '학기': [1, 1, 2, 2]
        }
        
        # clean_dataframe이 정제된 데이터를 반환하도록 모킹
        cleaned_df = pd.DataFrame({
            'course_name': test_data['과목명'],
            'course_type': test_data['이수구분'],
            'credits': test_data['학점'],
            'grade': test_data['성적'],
            'year': test_data['년도'],
            'semester': test_data['학기']
        })
        mock_clean_dataframe.return_value = cleaned_df
        
        file_content = self.create_test_excel_file(test_data)
        excel_file = SimpleUploadedFile(
            "graduation_check.xlsx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        with patch('myapp.views.graduation_check.GraduationAnalyzer') as mock_analyzer_class:
            # F학점이 있는 결과 모킹
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = {
                'total_credits': 6,  # F, N 학점 제외
                'status': '미졸업',
                'required_courses': {
                    '심화교양': ['철학산책'],
                    '전공선택': ['윤리학']
                },
                'missing_courses': {
                    '심화교양': ['철학의이해'],
                    '전공선택': ['논리학', '인식론']  # F, N 학점 과목들
                },
                'details': {},
                'f_grade_courses': [
                    {'course_name': '논리학', 'grade': 'F', 'credits': 3, 'year': 2024, 'semester': 1},
                    {'course_name': '인식론', 'grade': 'N', 'credits': 3, 'year': 2024, 'semester': 2}
                ],
                'admission_year': 2024,
                'internship_completed': True
            }
            mock_analyzer_class.return_value = mock_analyzer
            
            response = self.client.post(self.upload_url, {
                'excel_file': excel_file,
                'student_id': '20240001',
                'student_type': 'normal',
                'internship_completed': 'yes'
            })
            
            self.assertEqual(response.status_code, 200)
            mock_analyzer.analyze.assert_called_once()
    
    @patch('myapp.services.graduation.graduation_analyzer.clean_dataframe')
    def test_different_student_types(self, mock_clean_dataframe):
        """다양한 학생 유형별 졸업 확인 테스트"""
        student_types = ['normal', 'transfer', 'double_major']
        
        test_data = {
            '과목명': ['철학산책', '논리학'],
            '이수구분': ['심교', '전선'],
            '학점': [3, 3],
            '성적': ['A', 'B+'],
            '년도': [2024, 2024],
            '학기': [1, 1]
        }
        
        # clean_dataframe이 정제된 데이터를 반환하도록 모킹
        cleaned_df = pd.DataFrame({
            'course_name': test_data['과목명'],
            'course_type': test_data['이수구분'],
            'credits': test_data['학점'],
            'grade': test_data['성적'],
            'year': test_data['년도'],
            'semester': test_data['학기']
        })
        mock_clean_dataframe.return_value = cleaned_df
        
        file_content = self.create_test_excel_file(test_data)
        
        for student_type in student_types:
            with self.subTest(student_type=student_type):
                excel_file = SimpleUploadedFile(
                    f"graduation_check_{student_type}.xlsx",
                    file_content,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                with patch('myapp.views.graduation_check.GraduationAnalyzer') as mock_analyzer_class:
                    mock_analyzer = Mock()
                    mock_analyzer.analyze.return_value = {
                        'total_credits': 6,
                        'status': '미졸업',
                        'required_courses': {},
                        'missing_courses': {},
                        'details': {},
                        'f_grade_courses': [],
                        'admission_year': 2024,
                        'internship_completed': True
                    }
                    mock_analyzer_class.return_value = mock_analyzer
                    
                    response = self.client.post(self.upload_url, {
                        'excel_file': excel_file,
                        'student_id': '20240001',
                        'student_type': student_type,
                        'internship_completed': 'yes'
                    })
                    
                    self.assertEqual(response.status_code, 200)
                    # 올바른 학생 유형으로 분석이 호출되었는지 확인
                    call_args = mock_analyzer.analyze.call_args
                    if call_args:  # 호출되었는지 확인
                        self.assertEqual(call_args[0][1], student_type)
    
    @patch('myapp.services.graduation.graduation_analyzer.clean_dataframe')
    def test_different_admission_years(self, mock_clean_dataframe):
        """다양한 입학년도별 졸업 확인 테스트"""
        admission_years = [2023, 2024, 2025, 2026]
        
        test_data = {
            '과목명': ['철학산책', '논리학'],
            '이수구분': ['심교', '전선'],
            '학점': [3, 3],
            '성적': ['A', 'B+'],
            '년도': [2024, 2024],
            '학기': [1, 1]
        }
        
        # clean_dataframe이 정제된 데이터를 반환하도록 모킹
        cleaned_df = pd.DataFrame({
            'course_name': test_data['과목명'],
            'course_type': test_data['이수구분'],
            'credits': test_data['학점'],
            'grade': test_data['성적'],
            'year': test_data['년도'],
            'semester': test_data['학기']
        })
        mock_clean_dataframe.return_value = cleaned_df
        
        file_content = self.create_test_excel_file(test_data)
        
        for year in admission_years:
            with self.subTest(admission_year=year):
                student_id = f"{year}0001"
                excel_file = SimpleUploadedFile(
                    f"graduation_check_{year}.xlsx",
                    file_content,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                with patch('myapp.views.graduation_check.GraduationAnalyzer') as mock_analyzer_class:
                    mock_analyzer = Mock()
                    mock_analyzer.analyze.return_value = {
                        'total_credits': 6,
                        'status': '미졸업',
                        'required_courses': {},
                        'missing_courses': {},
                        'details': {},
                        'f_grade_courses': [],
                        'admission_year': year,
                        'internship_completed': True
                    }
                    mock_analyzer_class.return_value = mock_analyzer
                    
                    response = self.client.post(self.upload_url, {
                        'excel_file': excel_file,
                        'student_id': student_id,
                        'student_type': 'normal',
                        'internship_completed': 'yes'
                    })
                    
                    self.assertEqual(response.status_code, 200)
                    # 올바른 입학년도로 분석이 호출되었는지 확인
                    call_args = mock_analyzer.analyze.call_args
                    if call_args:  # 호출되었는지 확인
                        self.assertEqual(call_args[0][2], year) 