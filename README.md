# 건국대학교 철학과 졸업요건 체크 시스템

이 프로젝트는 건국대학교 철학과 학생들의 졸업요건을 확인하고 관리할 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 입학년도별 졸업요건 확인
- 학생 유형별(일반, 편입, 다전공, 부전공) 졸업요건 관리
- 이수과목 자동 체크
- 졸업요건 충족 현황 시각화
- Excel 파일을 통한 성적 데이터 업로드 및 분석

## 기술 스택

- Backend: Django 5.1.2
- Frontend: HTML, CSS, JavaScript, Bootstrap 5
- Database: SQLite (개발 환경)
- 데이터 처리: Pandas, NumPy
- 테스트: Pytest
- 배포: Gunicorn

## 프로젝트 구조

```
graduateCheck/
├── graduateCheck/          # 프로젝트 설정
│   ├── settings/          # 환경별 설정
│   ├── urls.py           # URL 라우팅
│   └── wsgi.py          # WSGI 설정
├── myapp/                 # 메인 애플리케이션
│   ├── models/           # 데이터 모델
│   ├── config/           # 설정 파일
│   │   └── requirements/ # 졸업요건 설정
│   ├── templates/        # HTML 템플릿
│   └── static/          # 정적 파일
├── static/               # 전역 정적 파일
├── media/                # 사용자 업로드 파일
├── tests/               # 테스트 코드
├── requirements.txt     # 프로젝트 의존성
└── manage.py           # Django 관리 스크립트
```

## 설치 및 실행

1. 저장소 클론
```bash
git clone [repository-url]
cd graduateCheck
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

5. 개발 서버 실행
```bash
python manage.py runserver
```

## 졸업요건 구성

- 공통 필수 과목
- 전공 필수 과목
- 전공 선택 과목
- 전공 기초 과목
- 총 이수학점
- 현장실습 요건
- 현장답사 요건

## 테스트 실행

```bash
pytest
```

## 기여 방법

1. 이슈 생성
2. 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 개발자

- 송영록