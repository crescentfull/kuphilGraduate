from django.shortcuts import render
import pandas as pd
from ..services.graduation.analyzer import GraduationAnalyzer

def analyze_graduation(request):
    if request.method == 'POST':
        try:
            excel_file = request.FILES['excel_file']
            student_id = request.POST.get('student_id')
            student_type = request.POST.get('student_type', 'normal')
            
            if not student_id:
                return render(request, 'upload.html', {'error': '학번을 입력해주세요.'})
            
            # 학번에서 입학년도 추출 (예: 201110207 -> 2011)
            admission_year = int(student_id[:4])
            
            df = pd.read_excel(excel_file)
            
            analyzer = GraduationAnalyzer()
            result = analyzer.analyze(df, student_type, admission_year)
            
            if 'error' in result:
                return render(request, 'upload.html', {'error': result['error']})
                
            return render(request, 'result.html', {'result': result})
            
        except Exception as e:
            return render(request, 'upload.html', {'error': str(e)})
    
    return render(request, 'upload.html') 