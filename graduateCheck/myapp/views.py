from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import pandas as pd
import os
from django.conf import settings
from django.views.decorators.http import require_http_methods
import uuid
import warnings
import numpy as np
from django.views.decorators.csrf import csrf_exempt
import json

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
    """데이터프레임 정제"""
    try:
        # 1. 컬럼명 정규화
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # 2. 필수 컬럼 확인 및 생성
        required_columns = ['과목명', '이수구분', '학점']
        for col in required_columns:
            if col not in df.columns:
                if col == '과목명':
                    df.loc[:, '과목명'] = df['교과목명']
                elif col == '이수구분':
                    df.loc[:, '이수구분'] = df['과목구분']
                elif col == '학점':
                    df.loc[:, '학점'] = df['학점수']
        
        # 3. 데이터 정제
        df = df.dropna(subset=['과목명', '이수구분', '학점']).copy()
        
        # 문자열 데이터만 strip() 적용
        if df['과목명'].dtype == 'object':
            df.loc[:, '과목명'] = df['과목명'].str.strip()
        if df['이수구분'].dtype == 'object':
            df.loc[:, '이수구분'] = df['이수구분'].str.strip()
            
        # 학점은 숫자로 변환
        df.loc[:, '학점'] = pd.to_numeric(df['학점'], errors='coerce')
        
        # 4. 과목명에서 띄어쓰기 제거 (문자열 데이터만)
        if df['과목명'].dtype == 'object':
            df.loc[:, '과목명'] = df['과목명'].str.replace(' ', '')
        
        # 5. '취득학점포기' 데이터 처리
        if '삭제구분' in df.columns:
            # '취득학점포기'가 아닌 데이터만 선택
            df = df[df['삭제구분'] != '취득학점포기'].copy()
        
        # 6. 컬럼명 영문으로 변경
        df = df.rename(columns={
            '과목명': 'course_name',
            '이수구분': 'course_type',
            '학점': 'credits'
        })
        
        return df
    except Exception as e:
        print(f"데이터 정제 중 오류 발생: {str(e)}")
        raise

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
        student_type = request.POST.get('student_type', 'normal')  # 기본값은 'normal'
        
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
            
            result = analyze_graduation_requirements(df, student_type)
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

def get_graduation_requirements(student_type):
    requirements = {
        'normal': {
            'common_required': {
                '심교': ['철학산책', '철학의이해'],
                '지교': 5  # 문과대학 지정교양 과목 5개
            },
            '전선': [
                '철학의문제들',
                '동양사상과현실문제',
                '논리학',
                '서양철학고전읽기',
                '동양철학고전읽기',
                '서양고중세철학',
                '학술답사Ⅰ',
                '학술답사Ⅱ',
                '학술답사Ⅲ',
                '중국철학의이해',
                '윤리학',
                '서양근세철학',
                '인식론',
                '형이상학',
                '한국철학의이해',
                '서양현대철학'
            ],
            '전선_min': 4,  # 전공선택 과목 중 4개 이상
            'internship_required': True
        },
        'transfer': {
            '전선': [
                '서양고중세철학',
                '학술답사Ⅰ',
                '학술답사Ⅱ',
                '학술답사Ⅲ',
                '중국철학의이해',
                '윤리학',
                '서양근세철학',
                '인식론',
                '형이상학',
                '한국철학의이해',
                '중국유학'
            ],
            '전선_min': 3  # 5개 중 3개 이상
        },
        'double': {
            'common_required': {
                '심교': ['철학산책', '철학의이해']
            },
            '전선': [
                '서양고중세철학',
                '중국철학의이해',
                '윤리학',
                '인식론',
                '서양근세철학',
                '한국철학의이해',
                '형이상학'
            ],
            '전선_min': 4  # 7개 중 4개 이상
        },
        'minor': {
            '전선': [
                '철학의문제들',
                '논리학',
                '중국철학의이해',
                '윤리학',
                '서양근세철학',
                '인식론',
                '형이상학',
                '한국철학의이해',
                '서양현대철학'
            ],
            '전선_min': 3  # 6개 중 3개 이상
        }
    }
    return requirements.get(student_type, {})

def analyze_graduation_requirements(df, student_type):
    requirements = get_graduation_requirements(student_type)
    result = {
        'total_credits': 0,
        'required_courses': {},
        'missing_courses': {},
        'status': '미졸업',
        'details': {}
    }
    
    try:
        # 총 이수학점 계산
        result['total_credits'] = df['credits'].sum()
        
        # 공통 필수 과목 체크 (일반학생, 다전공자)
        if 'common_required' in requirements:
            for category, courses in requirements['common_required'].items():
                if isinstance(courses, list):
                    for course in courses:
                        # 심교와 핵교를 같은 이수구분으로 처리
                        if category == '심교':
                            course_data = df[
                                (df['course_name'].str.contains(course, case=False, na=False)) & 
                                ((df['course_type'] == '심교') | (df['course_type'] == '핵교'))
                            ]
                        else:
                            course_data = df[
                                (df['course_name'].str.contains(course, case=False, na=False)) & 
                                (df['course_type'] == category)
                            ]
                        
                        if not course_data.empty:
                            if category not in result['required_courses']:
                                result['required_courses'][category] = []
                            result['required_courses'][category].append({
                                'course_name': course,
                                'category': category,
                                'credits': course_data['credits'].iloc[0]
                            })
                        else:
                            if category not in result['missing_courses']:
                                result['missing_courses'][category] = []
                            result['missing_courses'][category].append({
                                'course_name': course,
                                'category': category,
                                'credits': 3  # 기본 학점
                            })
                elif isinstance(courses, int):  # 지정교양 과목 수
                    liberal_arts_courses = df[df['course_type'] == '지교']
                    if len(liberal_arts_courses) >= courses:
                        if '지교' not in result['required_courses']:
                            result['required_courses']['지교'] = []
                        # 실제 이수한 지정교양 과목들을 추가
                        for _, course in liberal_arts_courses.iterrows():
                            result['required_courses']['지교'].append({
                                'course_name': course['course_name'],
                                'category': '지교',
                                'credits': course['credits']
                            })
                    else:
                        if '지교' not in result['missing_courses']:
                            result['missing_courses']['지교'] = []
                        # 이수한 지정교양 과목들을 추가
                        for _, course in liberal_arts_courses.iterrows():
                            result['missing_courses']['지교'].append({
                                'course_name': course['course_name'],
                                'category': '지교',
                                'credits': course['credits']
                            })
                        # 부족한 과목 수만큼 '미이수' 표시
                        for _ in range(courses - len(liberal_arts_courses)):
                            result['missing_courses']['지교'].append({
                                'course_name': '지정교양 미이수',
                                'category': '지교',
                                'credits': 3
                            })
        
        # 전공 과목 체크 (전선으로 통합)
        if '전선' in requirements:
            select_count = 0
            for course in requirements['전선']:
                course_data = df[
                    (df['course_name'].str.contains(course, case=False, na=False)) & 
                    (df['course_type'] == '전선')
                ]
                if not course_data.empty:
                    select_count += 1
                    if '전선' not in result['required_courses']:
                        result['required_courses']['전선'] = []
                    result['required_courses']['전선'].append({
                        'course_name': course,
                        'category': '전선',
                        'credits': course_data['credits'].iloc[0]
                    })
                else:
                    if '전선' not in result['missing_courses']:
                        result['missing_courses']['전선'] = []
                    result['missing_courses']['전선'].append({
                        'course_name': course,
                        'category': '전선',
                        'credits': 3  # 기본 학점
                    })
            
            if select_count >= requirements['전선_min']:
                result['details']['전선'] = '충족'
            else:
                result['details']['전선'] = '미충족'
        
        # 인턴십 체크 (일반학생)
        if requirements.get('internship_required', False):
            internship_courses = df[df['course_name'].str.contains('인턴십', case=False, na=False)]
            if not internship_courses.empty:
                result['details']['인턴십'] = '충족'
            else:
                result['details']['인턴십'] = '미충족'
        
        # 졸업 가능 여부 판단
        if (result['total_credits'] >= 130 and  # 총 이수학점 130학점 이상
            len(result['missing_courses']) == 0 and  # 모든 필수과목 이수
            all(status == '충족' for status in result['details'].values())):  # 모든 세부요건 충족
            result['status'] = '졸업가능'
        
        # 각 이수구분별 과목들을 가나다 순으로 정렬
        for category in result['required_courses']:
            result['required_courses'][category] = sorted(
                result['required_courses'][category],
                key=lambda x: x['course_name']
            )
        
        for category in result['missing_courses']:
            result['missing_courses'][category] = sorted(
                result['missing_courses'][category],
                key=lambda x: x['course_name']
            )
    
    except Exception as e:
        result['error'] = str(e)
        result['status'] = '오류'
    
    return result

@csrf_exempt
def analyze(request):
    if request.method == 'POST':
        try:
            excel_file = request.FILES['excel_file']
            student_type = request.POST.get('student_type', 'normal')
            
            # 파일 저장
            file_path = os.path.join(settings.MEDIA_ROOT, excel_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 졸업요건 분석
            result = analyze_graduation_requirements(df, student_type)
            
            # 파일 삭제
            os.remove(file_path)
            
            return render(request, 'result.html', {'result': result})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

def analyze_completed_courses(df):
    """이수한 과목 분석"""
    completed_courses = {}
    
    for _, row in df.iterrows():
        course_name = row['course_name']
        if course_name not in completed_courses:
            completed_courses[course_name] = {
                'course_name': course_name,
                'category': row['course_type'],
                'credits': row['credits']
            }
    
    return completed_courses

def process_excel(df, major, student_id):
    """엑셀 데이터 처리 및 졸업 요건 검사"""
    try:
        # 1. 데이터 정제
        df = clean_dataframe(df)
        
        # 2. 전공별 졸업 요건 가져오기
        requirements = get_graduation_requirements(major)
        
        # 3. 이수 과목 분석
        completed_courses = analyze_completed_courses(df)
        
        # 4. 필수 과목 검사
        required_courses = []
        missing_courses = []
        
        for course in requirements['required_courses']:
            if course['course_name'] in completed_courses:
                required_courses.append({
                    'course_name': course['course_name'],
                    'category': course['category'],
                    'credits': completed_courses[course['course_name']]['credits']
                })
            else:
                missing_courses.append({
                    'course_name': course['course_name'],
                    'category': course['category'],
                    'credits': course['credits']
                })
        
        # 5. 이수구분별 과목 그룹화 및 정렬
        def group_and_sort_courses(courses):
            # 이수구분별로 그룹화
            grouped = {}
            for course in courses:
                category = course['category']
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(course)
            
            # 각 그룹 내에서 과목명 오름차순 정렬
            for category in grouped:
                grouped[category] = sorted(grouped[category], key=lambda x: x['course_name'])
            
            return grouped
        
        required_courses_grouped = group_and_sort_courses(required_courses)
        missing_courses_grouped = group_and_sort_courses(missing_courses)
        
        # 6. 결과 반환
        return {
            'student_id': student_id,
            'major': major,
            'total_credits': sum(course['credits'] for course in completed_courses.values()),
            'required_credits': requirements['required_credits'],
            'required_courses': required_courses_grouped,
            'missing_courses': missing_courses_grouped,
            'elective_courses': sorted(completed_courses.values(), key=lambda x: x['course_name'])
        }
    except Exception as e:
        print(f"데이터 처리 중 오류 발생: {str(e)}")
        raise
