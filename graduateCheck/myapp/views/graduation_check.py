from django.shortcuts import render
import pandas as pd
from ..services.graduation.graduation_analyzer import GraduationAnalyzer

def analyze_graduation(request):
    if request.method == 'POST':
        try:
            excel_file = request.FILES['excel_file']
            student_id = request.POST.get('student_id')
            student_type = request.POST.get('student_type', 'normal')
            internship_completed = request.POST.get('internship_completed', 'no')
            
            if not student_id:
                return render(request, 'upload.html', {'error': '학번을 입력해주세요.'})
            
            # 학번에서 입학년도 추출 (예: 201110207 -> 2011)
            admission_year = int(student_id[:4])
            
            # 2024학번까지는 인턴십 이수 여부 확인
            if admission_year <= 2024 and not internship_completed:
                return render(request, 'upload.html', {'error': '2024학번까지는 인턴십 이수 여부를 선택해주세요.'})
            
            df = pd.read_excel(excel_file)
            
            analyzer = GraduationAnalyzer()
            result = analyzer.analyze(df, student_type, admission_year, internship_completed)
            
            if 'error' in result:
                return render(request, 'upload.html', {'error': result['error']})
            
            # 남은 학점 계산
            if student_type == 'normal':
                result['remaining_credits'] = 124 - result['total_credits']
            elif student_type == 'transfer':
                result['remaining_credits'] = 65 - result['total_credits']
            elif student_type == 'double':
                result['remaining_credits'] = 40 - result['total_credits']
            elif student_type == 'minor':
                result['remaining_credits'] = 24 - result['total_credits']
                
            return render(request, 'result.html', {
                'result': result,
                'student_type': student_type
            })
            
        except Exception as e:
            return render(request, 'upload.html', {'error': str(e)})
    
    return render(request, 'upload.html') 