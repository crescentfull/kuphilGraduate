import sys
sys.path.append('.')
import pandas as pd
from myapp.services.cleaner2 import ExcelStructureDetector, FlexibleCleaner
import re

# 파일 읽기
df = pd.read_excel('logs/취득학점확인원(이소라22).xlsx')

# 구조 감지
detector = ExcelStructureDetector()
structure = detector.detect_structure(df)

print("=== 감지된 구조 ===")
print(f"포맷 타입: {structure['format_type']}")
print(f"데이터 시작 행: {structure['data_start_row']}")
print()

# 과목구분 감지 테스트
print("=== 과목구분 감지 테스트 ===")
for i in range(3, 17):
    row = df.iloc[i]
    row_values = [str(cell).strip() for cell in row if pd.notnull(cell) and str(cell).strip()]
    
    course_type = None
    for j in range(min(3, len(row_values))):
        if row_values[j] in detector.course_types:
            course_type = row_values[j]
            break
    
    print(f"행 {i:2d}: 과목구분='{course_type}', 첫 3개 값: {row_values[:3]}")

print()
print("=== 과목 추출 상세 디버깅 ===")
cleaner = FlexibleCleaner()

# 행 3 테스트 (지교가 있는 행)
row3 = df.iloc[3]
row3_values = [str(cell).strip() for cell in row3 if pd.notnull(cell) and str(cell).strip()]
print(f"행 3 전체 데이터: {row3_values}")

# 수동으로 과목 추출 과정 시뮬레이션
print("\n=== 수동 과목 추출 시뮬레이션 ===")
i = 0
# 과목구분과 총학점 정보 스킵
while i < len(row3_values):
    if row3_values[i] in detector.course_types:
        print(f"과목구분 '{row3_values[i]}' 발견 at index {i}")
        i += 1
        # 총학점 정보 스킵
        while i < len(row3_values) and (
            re.match(r'^\d+\.\d+$', row3_values[i]) or 
            re.match(r'^\(\d+\.\d+\)$', row3_values[i])
        ):
            print(f"총학점 정보 '{row3_values[i]}' 스킵 at index {i}")
            i += 1
        break
    i += 1

print(f"과목 추출 시작 index: {i}")

# 학기 패턴 찾기
semester_count = 0
while i < len(row3_values):
    if re.match(r'^\d{2}/\d$', row3_values[i]):
        semester_count += 1
        print(f"학기 패턴 '{row3_values[i]}' 발견 at index {i}")
        # 다음 몇 개 값들 확인
        for j in range(i, min(i+8, len(row3_values))):
            print(f"  [{j}] {row3_values[j]}")
        i += 8  # 임시로 8개씩 건너뛰기
    else:
        i += 1

print(f"총 {semester_count}개의 학기 패턴 발견")

courses = cleaner._extract_courses_from_row(row3_values, "지정교양")
print(f"\n실제 추출된 과목 수: {len(courses)}")
for course in courses:
    print(f"  - {course['course_name']} ({course['credits']}학점, {course['grade']})") 