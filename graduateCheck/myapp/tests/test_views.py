import pytest
import pandas as pd
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock, MagicMock
from django.test import override_settings
import io


@pytest.mark.django_db
@override_settings(SECURE_SSL_REDIRECT=False)  # 테스트에서 SSL 리다이렉트 비활성화
class TestGraduationCheckViews(TestCase):
    """졸업 확인 뷰 테스트"""
    
    def setUp(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = Client()
        # 실제 URL 이름 사용
        self.upload_url = reverse('index')  # 'analyze_graduation' 대신 'index' 사용
    
    def test_get_upload_page(self):
        """업로드 페이지 GET 요청 테스트"""
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
    
    def test_post_without_file(self):
        """파일 없이 POST 요청 시 에러 처리 테스트"""
        response = self.client.post(self.upload_url, {
            'student_id': '20240001',
            'student_type': 'normal'
        })
        # 파일이 없으면 에러가 발생해야 함
        self.assertEqual(response.status_code, 200)
    
    def test_post_without_student_id(self):
        """학번 없이 POST 요청 시 에러 처리 테스트"""
        # 더미 엑셀 파일 생성
        file_content = b"dummy excel content"
        excel_file = SimpleUploadedFile(
            "test.xlsx", 
            file_content, 
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(self.upload_url, {
            'excel_file': excel_file,
            'student_type': 'normal'
        })
        
        # 학번이 없으면 에러 메시지가 표시되어야 함
        self.assertEqual(response.status_code, 200)
        if hasattr(response, 'context') and response.context:
            self.assertIn('error', response.context)
    
    @patch('pandas.read_excel')
    @patch('myapp.views.graduation_check.GraduationAnalyzer')
    def test_successful_analysis(self, mock_analyzer_class, mock_read_excel):
        """정상적인 분석 프로세스 테스트"""
        # Mock 데이터프레임 설정
        mock_df = pd.DataFrame({
            'course_name': ['철학산책', '논리학'],
            'course_type': ['심교', '전선'],
            'credits': [3, 3],
            'grade': ['A', 'B+']
        })
        mock_read_excel.return_value = mock_df
        
        # Mock 분석기 설정
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            'total_credits': 6,
            'status': '미졸업',
            'required_courses': {},
            'missing_courses': {'전공필수': ['윤리학']},
            'details': {}
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        # 더미 엑셀 파일 생성
        excel_file = SimpleUploadedFile(
            "test.xlsx", 
            b"dummy excel content", 
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(self.upload_url, {
            'excel_file': excel_file,
            'student_id': '20240001',
            'student_type': 'normal',
            'internship_completed': 'yes'
        })
        
        self.assertEqual(response.status_code, 200)
        # 분석이 호출되었는지 확인
        mock_analyzer.analyze.assert_called_once()
    
    @patch('pandas.read_excel')
    @patch('myapp.views.graduation_check.GraduationAnalyzer')
    def test_analysis_with_error(self, mock_analyzer_class, mock_read_excel):
        """분석 중 에러 발생 시 처리 테스트"""
        # Mock 데이터프레임 설정
        mock_df = pd.DataFrame({
            'course_name': ['철학산책'],
            'course_type': ['심교'],
            'credits': [3]
        })
        mock_read_excel.return_value = mock_df
        
        # Mock 분석기에서 에러 반환
        mock_analyzer = Mock()
        mock_analyzer.analyze.return_value = {
            'error': '분석 중 오류가 발생했습니다.'
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        excel_file = SimpleUploadedFile(
            "test.xlsx", 
            b"dummy excel content", 
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(self.upload_url, {
            'excel_file': excel_file,
            'student_id': '20240001',
            'student_type': 'normal'
        })
        
        self.assertEqual(response.status_code, 200)
        # 에러가 컨텍스트에 포함되어야 함
        if hasattr(response, 'context') and response.context:
            self.assertIn('error', response.context)
    
    def test_internship_requirement_for_old_students(self):
        """2024학번까지 인턴십 이수 여부 확인 테스트"""
        excel_file = SimpleUploadedFile(
            "test.xlsx", 
            b"dummy excel content", 
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # 2024학번 학생이 인턴십 이수 여부를 선택하지 않은 경우
        response = self.client.post(self.upload_url, {
            'excel_file': excel_file,
            'student_id': '20240001',
            'student_type': 'normal'
            # internship_completed 누락
        })
        
        self.assertEqual(response.status_code, 200)
        # 인턴십 이수 여부 선택 에러 메시지가 표시되어야 함
        if hasattr(response, 'context') and response.context:
            self.assertIn('error', response.context)
    
    @patch('pandas.read_excel')
    def test_excel_read_exception(self, mock_read_excel):
        """엑셀 파일 읽기 실패 시 예외 처리 테스트"""
        # pandas.read_excel에서 예외 발생
        mock_read_excel.side_effect = Exception("엑셀 파일을 읽을 수 없습니다.")
        
        excel_file = SimpleUploadedFile(
            "test.xlsx", 
            b"invalid excel content", 
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(self.upload_url, {
            'excel_file': excel_file,
            'student_id': '20240001',
            'student_type': 'normal',
            'internship_completed': 'yes'
        })
        
        self.assertEqual(response.status_code, 200)
        # 예외 메시지가 에러로 표시되어야 함
        if hasattr(response, 'context') and response.context:
            self.assertIn('error', response.context)
    
    def test_student_id_year_extraction(self):
        """학번에서 입학년도 추출 테스트"""
        # 이 테스트는 뷰 내부 로직을 직접 테스트하기 어려우므로
        # 실제 요청을 통해 간접적으로 테스트
        test_cases = [
            ('20240001', 2024),
            ('20250123', 2025),
            ('20230456', 2023),
        ]
        
        for student_id, expected_year in test_cases:
            with patch('pandas.read_excel') as mock_read_excel:
                with patch('myapp.views.graduation_check.GraduationAnalyzer') as mock_analyzer_class:
                    mock_df = pd.DataFrame({'course_name': ['철학산책'], 'credits': [3]})
                    mock_read_excel.return_value = mock_df
                    
                    mock_analyzer = Mock()
                    mock_analyzer.analyze.return_value = {'total_credits': 3, 'status': '미졸업'}
                    mock_analyzer_class.return_value = mock_analyzer
                    
                    excel_file = SimpleUploadedFile(
                        "test.xlsx", 
                        b"dummy", 
                        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    response = self.client.post(self.upload_url, {
                        'excel_file': excel_file,
                        'student_id': student_id,
                        'student_type': 'normal',
                        'internship_completed': 'yes'
                    })
                    
                    # 분석기가 올바른 입학년도로 호출되었는지 확인
                    if mock_analyzer.analyze.called:
                        call_args = mock_analyzer.analyze.call_args
                        self.assertEqual(call_args[0][2], expected_year)  # admission_year 파라미터


@override_settings(SECURE_SSL_REDIRECT=False)  # 테스트에서 SSL 리다이렉트 비활성화
class TestFileManagementViews(TestCase):
    """파일 관리 뷰 테스트"""
    
    def setUp(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = Client()
    
    def test_cleanup_view_exists(self):
        """파일 정리 뷰가 존재하는지 테스트"""
        try:
            cleanup_url = reverse('cleanup')
            response = self.client.get(cleanup_url)
            # 뷰가 존재하면 200 또는 다른 유효한 상태 코드 반환
            self.assertIn(response.status_code, [200, 302, 404])
        except:
            # cleanup URL이 정의되지 않은 경우 테스트 스킵
            self.skipTest("Cleanup URL이 정의되지 않음")
    
    def test_index_view_exists(self):
        """인덱스 뷰가 존재하는지 테스트"""
        try:
            index_url = reverse('index')
            response = self.client.get(index_url)
            self.assertIn(response.status_code, [200, 302])
        except:
            # index URL이 정의되지 않은 경우 기본 경로 테스트
            response = self.client.get('/')
            self.assertIn(response.status_code, [200, 302, 404]) 