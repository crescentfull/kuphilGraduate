import sys
sys.path.append('.')
from myapp.services.graduation.graduation_analyzer import GraduationAnalyzer
import pandas as pd

# 파일 읽기
df = pd.read_excel('logs/취득학점확인원(이소라22).xlsx')

# 졸업요건 분석
analyzer = GraduationAnalyzer()
result = analyzer.analyze(df, student_type='single', admission_year=2022, internship_completed='no')

print('=== 졸업요건 분석 결과 ===')
print(f'결과 키들: {list(result.keys())}')
print()

if 'total_credits' in result:
    print(f'총 취득학점: {result["total_credits"]}학점')

if 'is_graduated' in result:
    print(f'졸업 가능 여부: {"졸업 가능" if result["is_graduated"] else "미졸업"}')
elif 'graduation_status' in result:
    print(f'졸업 상태: {result["graduation_status"]}')

print()

if 'categories' in result:
    print('영역별 현황:')
    for category, info in result['categories'].items():
        if isinstance(info, dict) and 'satisfied' in info:
            status = "충족" if info["satisfied"] else "미충족"
            earned = info.get("earned", "?")
            required = info.get("required", "?")
            print(f'{category}: {earned}/{required}학점 ({status})')
        else:
            print(f'{category}: {info}')

print()
print('전체 결과:')
print(result) 