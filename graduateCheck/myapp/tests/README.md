# 졸업 확인 시스템 테스트 가이드

이 디렉토리는 졸업 확인 시스템의 테스트 코드를 포함합니다.

## 테스트 파일 구조

```
myapp/tests/
├── conftest.py          # pytest 설정 및 픽스처
├── test_models.py       # 모델 테스트
├── test_services.py     # 서비스 로직 테스트
├── test_views.py        # 뷰 테스트
├── test_integration.py  # 통합 테스트
├── test_utils.py        # 유틸리티 함수 테스트
└── README.md           # 이 파일
```

## 테스트 실행 방법

### 1. 모든 테스트 실행
```bash
# Django 테스트 러너 사용
python manage.py test myapp.tests

# pytest 사용 (권장)
pytest myapp/tests/
```

### 2. 특정 테스트 파일 실행
```bash
# 모델 테스트만 실행
pytest myapp/tests/test_models.py

# 뷰 테스트만 실행
pytest myapp/tests/test_views.py

# 서비스 테스트만 실행
pytest myapp/tests/test_services.py
```

### 3. 특정 테스트 클래스 실행
```bash
# 졸업요건 관리자 테스트만 실행
pytest myapp/tests/test_models.py::TestGraduationRequirementManager

# 졸업 분석기 테스트만 실행
pytest myapp/tests/test_services.py::TestGraduationAnalyzer
```

### 4. 특정 테스트 메서드 실행
```bash
# 특정 테스트 메서드만 실행
pytest myapp/tests/test_models.py::TestGraduationRequirementManager::test_get_requirement_2024_normal
```

### 5. 커버리지와 함께 실행
```bash
# 커버리지 측정과 함께 테스트 실행
pytest --cov=myapp myapp/tests/

# HTML 커버리지 리포트 생성
pytest --cov=myapp --cov-report=html myapp/tests/
```

## 테스트 옵션

### 상세한 출력
```bash
# 상세한 출력으로 테스트 실행
pytest -v myapp/tests/

# 매우 상세한 출력
pytest -vv myapp/tests/
```

### 실패한 테스트만 재실행
```bash
# 마지막 실행에서 실패한 테스트만 재실행
pytest --lf myapp/tests/

# 실패한 테스트와 새로 추가된 테스트 실행
pytest --ff myapp/tests/
```

### 병렬 실행
```bash
# pytest-xdist 플러그인 설치 후 병렬 실행
pip install pytest-xdist
pytest -n auto myapp/tests/
```

## 테스트 카테고리

### 1. 단위 테스트 (Unit Tests)
- **test_models.py**: 모델 클래스와 메서드 테스트
- **test_services.py**: 비즈니스 로직 테스트
- **test_utils.py**: 유틸리티 함수 테스트

### 2. 통합 테스트 (Integration Tests)
- **test_integration.py**: 전체 시스템 플로우 테스트

### 3. 뷰 테스트 (View Tests)
- **test_views.py**: HTTP 요청/응답 테스트

## 주요 테스트 시나리오

### 모델 테스트
- 졸업요건 조회 기능
- 학번별 요건 차이 확인
- 데이터클래스 필드 검증

### 서비스 테스트
- 과목명/구분 매핑 기능
- 졸업 분석 로직
- F학점 처리
- 에러 핸들링

### 뷰 테스트
- 파일 업로드 처리
- 학번 유효성 검사
- 인턴십 요구사항 확인
- 에러 응답 처리

### 통합 테스트
- 전체 졸업 확인 플로우
- 다양한 학생 유형별 테스트
- 입학년도별 요건 적용

## 테스트 데이터

테스트에서 사용하는 주요 데이터:

### 샘플 과목 데이터
```python
{
    'course_name': ['철학산책', '논리학', '윤리학'],
    'course_type': ['심교', '전선', '전선'],
    'credits': [3, 3, 3],
    'grade': ['A', 'B+', 'A']
}
```

### 테스트 학번
- 2024학번: `20240001`
- 2025학번: `20250123`
- 2023학번: `20230456`

## Mock 사용

테스트에서는 다음과 같은 외부 의존성을 모킹합니다:

- `pandas.read_excel`: 엑셀 파일 읽기
- `GraduationAnalyzer.analyze`: 졸업 분석 로직
- `clean_dataframe`: 데이터 정제 함수

## 주의사항

1. **데이터베이스**: Django 테스트는 임시 데이터베이스를 사용합니다.
2. **파일 업로드**: 실제 파일 대신 `SimpleUploadedFile`을 사용합니다.
3. **외부 의존성**: Mock을 사용하여 외부 서비스 호출을 시뮬레이션합니다.

## 테스트 추가 가이드

새로운 테스트를 추가할 때:

1. 적절한 테스트 파일을 선택하거나 새로 생성
2. 테스트 클래스와 메서드에 명확한 이름 사용
3. 독립적인 테스트 작성 (다른 테스트에 의존하지 않음)
4. 적절한 assertion 사용
5. 필요시 setUp/tearDown 메서드 활용

## 문제 해결

### 일반적인 문제들

1. **ImportError**: 모듈 경로 확인
2. **Database Error**: `@pytest.mark.django_db` 데코레이터 추가
3. **Mock 관련 오류**: import 경로와 패치 대상 확인

### 디버깅

```bash
# 디버깅 모드로 테스트 실행
pytest --pdb myapp/tests/

# 특정 지점에서 중단
pytest --pdb-trace myapp/tests/
``` 