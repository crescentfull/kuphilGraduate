import sys
sys.path.append('.')
import pandas as pd
from myapp.services.cleaner2 import clean_dataframe_v2

# 파일 읽기
df = pd.read_excel('logs/취득학점확인원(이소라22).xlsx')
cleaned_df = clean_dataframe_v2(df)

print(f'추출된 과목 수: {len(cleaned_df)}')
print()

# 현대인의다이어트 과목 찾기
diet_courses = cleaned_df[cleaned_df['course_name'].str.contains('다이어트', na=False)]
if len(diet_courses) > 0:
    print('현대인의다이어트 과목 발견:')
    for _, row in diet_courses.iterrows():
        print(f'  - {row["course_name"]} ({row["course_type"]}, {row["credits"]}학점, {row["grade"]})')
else:
    print('현대인의다이어트 과목을 찾을 수 없습니다.')

print()
print('심화교양 과목들:')
shimgyo = cleaned_df[cleaned_df['course_type'] == '심화교양']
for _, row in shimgyo.iterrows():
    print(f'  - {row["course_name"]} ({row["credits"]}학점, {row["grade"]})')

print()
print(f'심화교양 과목 수: {len(shimgyo)}개') 