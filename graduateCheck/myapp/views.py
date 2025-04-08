from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import os
from django.conf import settings
from django.views.decorators.http import require_http_methods
import uuid
import warnings
import numpy as np

# openpyxl 경고 메시지 숨기기
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def explore_headers(df):
    """엑셀 파일의 헤더(컬럼명) 탐색"""
    headers = df.columns.tolist()
    print("탐색된 헤더:", headers)
    return headers

def parse_grade_table(df):
    """성적표 형식의 엑셀 파일에서 실제 데이터 시작 위치를 찾아 헤더 재설정"""
    start_idx = None

    # ❶ 이수구분/과목명 등의 키워드가 포함된 행 탐색
    for idx, row in df.iterrows():
        row_text = ''.join(str(cell) for cell in row if pd.notnull(cell))
        if '이수구분' in row_text and '과목' in row_text:
            start_idx = idx
            break

    if start_idx is None:
        raise ValueError("성적표 헤더를 찾을 수 없습니다.")

    # ❷ 해당 행을 헤더로 지정
    new_header = df.iloc[start_idx]
    data = df.iloc[start_idx + 1:].copy()
    data.columns = new_header
    data.reset_index(drop=True, inplace=True)

    print(f"성적표 파싱 완료: {len(data)}행의 데이터 추출")
    return data

def clean_dataframe(df):
    """엑셀 데이터 정제 함수"""
    # 1. 헤더 탐색
    headers = explore_headers(df)
    
    # 2. 컬럼명 정제
    df.columns = df.columns.str.strip().str.lower()
    
    # 3. 빈 컬럼 제거
    df = df.dropna(axis=1, how='all')
    
    # 4. 모든 행이 NaN인 행 제거
    df = df.dropna(how='all')
    
    # 5. 컬럼명 매핑
    column_mapping = {
        # 학점 관련 컬럼
        '학점': 'credits',
        '이수학점': 'credits',
        '학점수': 'credits',
        'credits': 'credits',
        'credit': 'credits',
        # 과목명 관련 컬럼
        '과목명': 'course_name',
        '과목': 'course_name',
        '교과목명': 'course_name',
        'course': 'course_name',
        'course name': 'course_name',
        # 과목유형 관련 컬럼
        '과목유형': 'course_type',
        '유형': 'course_type',
        'type': 'course_type',
        'course type': 'course_type',
        # 이수구분 관련 컬럼
        '이수구분': 'course_type',
        '구분': 'course_type',
        'classification': 'course_type'
    }
    
    # 6. 컬럼명 변경
    df = df.rename(columns=column_mapping)
    
    # 7. 필요한 컬럼이 있는지 확인
    required_columns = ['credits', 'course_name']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")
    
    # 8. 데이터 타입 변환
    df['credits'] = pd.to_numeric(df['credits'], errors='coerce')
    
    # 9. NaN 값 처리
    df = df.dropna(subset=['credits', 'course_name'])
    
    print("정제 후 컬럼:", df.columns.tolist())
    return df

def filter_keyword_rows(df, keyword_column, keywords):
    """특정 키워드가 포함된 행 필터링"""
    if keyword_column not in df.columns:
        raise ValueError(f"키워드 검색을 위한 컬럼 '{keyword_column}'이 없습니다.")
    
    # 대소문자 구분 없이 키워드 검색
    filtered_df = df[df[keyword_column].str.contains('|'.join(keywords), case=False, na=False)]
    print(f"키워드 '{keywords}'로 필터링된 행 수: {len(filtered_df)}")
    return filtered_df

def upload_file(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}_{excel_file.name}"
        file_path = os.path.join(settings.MEDIA_ROOT, unique_filename)
        
        # 파일 저장
        with open(file_path, 'wb+') as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)
        
        # 세션에 파일 경로 저장
        request.session['uploaded_file'] = file_path
        
        # 엑셀 파일 분석
        try:
            # 1. 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            print("원본 데이터 행 수:", len(df))
            
            # 2. 성적표 형식 파싱 시도
            try:
                df = parse_grade_table(df)
                print("성적표 형식으로 파싱 완료")
            except Exception as e:
                print(f"성적표 형식 파싱 실패: {str(e)}")
                print("기본 형식으로 처리합니다.")
            
            # 3. 데이터 정제
            df = clean_dataframe(df)
            print("정제 후 데이터 행 수:", len(df))
            
            # 4. 키워드로 필터링 (예: 전공필수 과목만 필터링)
            try:
                # 과목유형 컬럼이 있으면 키워드로 필터링
                if 'course_type' in df.columns:
                    # 실제 이수구분 키워드로 필터링
                    df = filter_keyword_rows(df, 'course_type', ['지교', '전선', '일선', '기교', '핵교', '일교', '심교'])
                    print("키워드 필터링 후 데이터 행 수:", len(df))
            except Exception as e:
                print(f"키워드 필터링 중 오류 발생: {str(e)}")
                # 필터링 실패해도 계속 진행
            
            result = analyze_graduation_requirements(df)
            return render(request, 'result.html', {'result': result})
        except Exception as e:
            # 에러 발생 시 파일 삭제
            if os.path.exists(file_path):
                os.remove(file_path)
            return render(request, 'upload.html', {'error': str(e)})
    
    return render(request, 'upload.html')

@require_http_methods(["GET"])
def cleanup_files(request):
    """세션 종료 시 업로드된 파일 삭제"""
    file_path = request.session.get('uploaded_file')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return HttpResponse(status=200)

def analyze_graduation_requirements(df):
    # 필수 과목 목록 (실제 이수구분에 맞게 수정)
    required_courses = {
        '전선': ['인식론', '자료구조', '알고리즘', '운영체제', '데이터베이스'],
        '지교': ['대학영어', '대학수학', '글쓰기'],
        '핵교': ['철학의 이해', '윤리학', '논리학']
    }
    
    # 결과 초기화
    result = {
        'total_credits': 0,
        'required_courses': [],
        'missing_courses': [],
        'status': '미졸업'
    }
    
    try:
        # 총 이수학점 계산
        result['total_credits'] = df['credits'].sum()
        
        # 필수과목 이수 현황 체크
        for category, courses in required_courses.items():
            for course in courses:
                # 키워드가 포함된 행 탐색
                course_data = df[df['course_name'].str.contains(course, case=False, na=False)]
                if not course_data.empty:
                    result['required_courses'].append({
                        'course_name': course,
                        'category': category
                    })
                else:
                    result['missing_courses'].append({
                        'course_name': course,
                        'category': category
                    })
        
        # 졸업 가능 여부 판단
        if (result['total_credits'] >= 130 and  # 총 이수학점 130학점 이상
            len(result['missing_courses']) == 0):  # 모든 필수과목 이수
            result['status'] = '졸업가능'
    
    except Exception as e:
        result['error'] = str(e)
        result['status'] = '오류'
    
    return result
