import pandas as pd
import re

# 파일 읽기
df = pd.read_excel('logs/취득학점확인원(이소라22).xlsx')

print('=== 행별 과목 패턴 분석 ===')
for i in range(3, 17):
    row = df.iloc[i]
    values = [str(cell) for cell in row if pd.notnull(cell) and str(cell).strip()]
    
    # 과목구분 제외하고 한글 과목명 찾기
    korean_courses = [v for v in values if len(v) >= 2 and re.search(r'[가-힣]', v) 
                     and v not in ['기교', '심교', '지교', '지필', '전선', '다선', '다지', '다필', '일선']]
    
    # 학기 패턴 찾기
    semester_patterns = [v for v in values if re.match(r'\d{2}/\d', v)]
    
    print(f'행 {i:2d}: 학기패턴 {len(semester_patterns)}개, 한글과목 {len(korean_courses)}개')
    if len(korean_courses) > 0:
        print(f'     과목들: {korean_courses}')
    print()

print('=== 특정 행 상세 분석 ===')
# 행 6 상세 분석 (많은 과목이 있는 것 같은 행)
row6 = df.iloc[6]
values6 = [f'[{i}]{str(cell)}' for i, cell in enumerate(row6) if pd.notnull(cell)]
print('행 6 전체 데이터:')
for val in values6:
    print(val) 