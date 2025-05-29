import sys
sys.path.append('.')
import pandas as pd
from myapp.services.cleaner2 import FlexibleCleaner

# 파일 읽기
df = pd.read_excel('logs/취득학점확인원(이소라22).xlsx')
cleaner = FlexibleCleaner()

print("=== 과목구분 추적 테스트 ===")
current_course_type = None

for idx in range(3, 17):
    row = df.iloc[idx]
    row_values = [str(cell).strip() for cell in row if pd.notnull(cell) and str(cell).strip()]
    
    # 과목구분 찾기
    course_type = None
    for i in range(min(3, len(row_values))):
        if row_values[i] in cleaner.detector.course_types:
            course_type = row_values[i]
            current_course_type = course_type  # 현재 과목구분 업데이트
            break
    
    # 과목구분이 없으면 이전 과목구분 사용
    if not course_type and current_course_type:
        course_type = current_course_type
    
    print(f'행 {idx:2d}: 감지된 과목구분={course_type:8s}, 현재 추적중={current_course_type:8s}')
    
    if course_type:
        # 과목 추출 테스트
        extracted_courses = cleaner._extract_courses_from_row(row_values, course_type)
        print(f'      추출된 과목 수: {len(extracted_courses)}')
        for course in extracted_courses:
            print(f'        - {course["course_name"]}')
    print() 