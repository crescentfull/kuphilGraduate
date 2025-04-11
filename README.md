# 대학 졸업요건 점검 시스템

## 프로젝트 개요
이 프로젝트는 대학생들이 자신의 성적표 엑셀 파일을 업로드하여 졸업요건 충족 여부를 자동으로 확인할 수 있는 웹 애플리케이션입니다. 사용자의 학번에 따라 다른 졸업요건을 적용하며, 학점 계산, 필수 과목 이수 여부, 기타 졸업요건 충족 여부 등을 종합적으로 분석합니다.

## 주요 기능
- 성적표 엑셀 파일 업로드 및 분석
- 학번별 다른 졸업요건 적용 (2024학번 이전/2025학번 이후)
- 이수 과목, 미이수 필수 과목 확인
- 전공/교양 학점 계산 및 분석
- 영어 성적 요건, 인턴십, 캡스톤 프로젝트 등 추가 요건 확인

## 기술 스택
- **백엔드**: Django 5.0.3
- **데이터 분석**: Pandas 2.2.1
- **엑셀 처리**: Openpyxl 3.1.2
- **테스트**: Pytest 8.0.2, Pytest-Django 4.8.0

## 설치 방법
1. 저장소 클론
   ```
   git clone https://github.com/yourusername/kuPhilGraudate.git
   cd kuPhilGraudate
   ```

2. 가상환경 생성 및 활성화
   ```
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 필요 패키지 설치
   ```
   pip install -r requirements.txt
   ```

4. 데이터베이스 마이그레이션
   ```
   cd graduateCheck
   python manage.py migrate
   ```

5. 개발 서버 실행
   ```
   python manage.py runserver
   ```

## 사용 방법
1. 웹 브라우저에서 `http://localhost:8000` 접속
2. 학사정보시스템에서 다운로드한 성적 엑셀 파일 업로드
3. 학번이 자동으로 감지되지 않을 경우, 입학년도 선택
4. '분석 시작' 버튼 클릭
5. 분석 결과 확인 (이수 과목, 미이수 필수 과목, 학점 계산 등)

## 프로젝트 구조
```
graduateCheck/
├── myapp/                     # 앱 디렉토리
│   ├── services/              # 비즈니스 로직
│   │   ├── graduation/        # 졸업요건 관련 서비스
│   │   └── excel/             # 엑셀 파일 처리 서비스
│   ├── views/                 # 뷰 함수
│   ├── models/                # 데이터 모델
│   ├── templates/             # HTML 템플릿
│   │   ├── base.html          # 기본 템플릿
│   │   ├── upload.html        # 업로드 페이지
│   │   └── result.html        # 결과 페이지
│   └── tests/                 # 테스트 코드
├── static/                    # 정적 파일
├── media/                     # 사용자 업로드 파일
└── graduateCheck/             # 프로젝트 설정
```

## 테스트
```
pytest
```

## 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스
MIT License

## 개발자
- 송영록