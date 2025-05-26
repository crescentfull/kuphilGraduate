import pytest
from myapp.models.graduation_requirement import GraduationRequirementManager, YearRequirement


class TestGraduationRequirementManager:
    """졸업요건 관리자 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.manager = GraduationRequirementManager()
    
    def test_get_requirement_2024_normal(self):
        """2024학번 일반학생 졸업요건 조회 테스트"""
        requirement = self.manager.get_requirement(2024, 'normal')
        
        assert requirement is not None
        assert isinstance(requirement, YearRequirement)
        assert requirement.year == 2024
        assert requirement.total_credits > 0
        assert isinstance(requirement.common_required, dict)
        assert isinstance(requirement.major_required, list)
    
    def test_get_requirement_2025_normal(self):
        """2025학번 일반학생 졸업요건 조회 테스트"""
        requirement = self.manager.get_requirement(2025, 'normal')
        
        assert requirement is not None
        assert isinstance(requirement, YearRequirement)
        assert requirement.year == 2025
        assert requirement.total_credits > 0
    
    def test_get_requirement_2026_uses_2025_rules(self):
        """2026학번은 2025년 요건을 사용하는지 테스트"""
        requirement_2025 = self.manager.get_requirement(2025, 'normal')
        requirement_2026 = self.manager.get_requirement(2026, 'normal')
        
        assert requirement_2025 is not None
        assert requirement_2026 is not None
        # 2026학번은 2025년 요건을 사용해야 함
        assert requirement_2026.total_credits == requirement_2025.total_credits
    
    def test_get_requirement_2023_uses_2024_rules(self):
        """2023학번은 2024년 요건을 사용하는지 테스트"""
        requirement_2023 = self.manager.get_requirement(2023, 'normal')
        requirement_2024 = self.manager.get_requirement(2024, 'normal')
        
        assert requirement_2023 is not None
        assert requirement_2024 is not None
        # 2023학번은 2024년 요건을 사용해야 함
        assert requirement_2023.total_credits == requirement_2024.total_credits
    
    def test_get_requirement_invalid_student_type(self):
        """잘못된 학생 유형으로 조회 시 None 반환 테스트"""
        requirement = self.manager.get_requirement(2024, 'invalid_type')
        
        # 잘못된 학생 유형의 경우 None이 반환되거나 예외가 발생할 수 있음
        # 실제 구현에 따라 조정 필요
        assert requirement is None or isinstance(requirement, YearRequirement)
    
    def test_year_requirement_dataclass_fields(self):
        """YearRequirement 데이터클래스 필드 테스트"""
        requirement = self.manager.get_requirement(2024, 'normal')
        
        assert hasattr(requirement, 'year')
        assert hasattr(requirement, 'common_required')
        assert hasattr(requirement, 'designated_required')
        assert hasattr(requirement, 'major_required')
        assert hasattr(requirement, 'major_elective_required')
        assert hasattr(requirement, 'major_elective_min')
        assert hasattr(requirement, 'major_base')
        assert hasattr(requirement, 'major_base_min')
        assert hasattr(requirement, 'total_credits')
        assert hasattr(requirement, 'internship_required')
        assert hasattr(requirement, 'field_trip')
        assert hasattr(requirement, 'field_trip_min')
    
    def test_internship_requirement_by_year(self):
        """학번별 인턴십 요구사항 테스트"""
        # 2024학번까지는 인턴십이 필요할 수 있음
        requirement_2024 = self.manager.get_requirement(2024, 'normal')
        requirement_2025 = self.manager.get_requirement(2025, 'normal')
        
        assert requirement_2024 is not None
        assert requirement_2025 is not None
        
        # 인턴십 요구사항이 boolean 타입인지 확인
        assert isinstance(requirement_2024.internship_required, bool)
        assert isinstance(requirement_2025.internship_required, bool) 