import pandas as pd

def find_data_start_row(df: pd.DataFrame) -> int:
    """실제 데이터가 시작되는 행을 찾습니다."""
    for idx, row in df.iterrows():
        row_text = ''.join(str(cell) for cell in row if pd.notnull(cell))
        # 이수구분과 과목이 포함된 행 찾기
        if ('이수구분' in row_text or '과목구분' in row_text) and ('과목' in row_text or '교과목' in row_text):
            return idx
    raise ValueError("성적표 헤더를 찾을 수 없습니다.")

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """성적표 데이터프레임 정제"""
    try:
        # 학년도, 학기, 이수구분(과목구분), 과목명, 학점 관련 열 찾기
        columns_data = {
            'year': None,
            'semester': None,
            'course_type': None,
            'course_name': None,
            'credits': None,
            'grade': None
        }
        
        # 실제 데이터 시작 행 찾기 (10번째 행부터 시작되는 경우가 많음)
        start_row = 10
        for i in range(5, 20):  # 넉넉하게 5~20 행 사이에서 검색
            row = df.iloc[i]
            # 과목 정보가 있는 행인지 확인 (학년도, 학기, 이수구분, 과목명 등)
            if not pd.isna(row.iloc[1]) and str(row.iloc[1]).isdigit() and '학기' in str(row.iloc[3]):
                start_row = i
                break

        # 각 열의 의미 파악
        for col_idx in range(df.shape[1]):
            col_name = df.columns[col_idx]
            col_values = df.iloc[start_row:start_row+10, col_idx].astype(str)
            col_joined = ' '.join([str(v) for v in col_values if not pd.isna(v)])
            
            # 열 데이터 분석
            if col_idx == 1 and any(str(v).isdigit() for v in col_values if not pd.isna(v)):
                columns_data['year'] = col_idx
            elif col_idx == 3 and any('학기' in str(v) for v in col_values if not pd.isna(v)):
                columns_data['semester'] = col_idx
            elif col_idx == 8 and any(v in ['전선', '기교', '지교', '핵교', '일교', '일선'] for v in col_values if not pd.isna(v)):
                columns_data['course_type'] = col_idx
            elif col_idx in range(17, 20) and any(len(str(v)) > 3 for v in col_values if not pd.isna(v)):
                columns_data['course_name'] = col_idx
            elif col_idx in range(30, 33) and any(str(v).isdigit() or str(v).replace('.', '').isdigit() for v in col_values if not pd.isna(v)):
                columns_data['credits'] = col_idx
            elif col_idx in range(33, 36) and any(v in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F', 'P'] for v in col_values if not pd.isna(v)):
                columns_data['grade'] = col_idx
        
        # 필요한 열을 다 찾았는지 확인
        if None in columns_data.values():
            missing_cols = [k for k, v in columns_data.items() if v is None]
            print(f"다음 열들을 찾지 못했습니다: {missing_cols}")
            print(f"각 열 인덱스: {columns_data}")
            
            # 기본값 설정
            if columns_data['year'] is None:
                columns_data['year'] = 1
            if columns_data['semester'] is None:
                columns_data['semester'] = 3
            if columns_data['course_type'] is None:
                columns_data['course_type'] = 8
            if columns_data['course_name'] is None:
                columns_data['course_name'] = 18
            if columns_data['credits'] is None:
                columns_data['credits'] = 31
            if columns_data['grade'] is None:
                columns_data['grade'] = 34
            
            print(f"기본값으로 설정된 열 인덱스: {columns_data}")
        
        # 추출된 열 인덱스로 새 데이터프레임 생성
        new_df = pd.DataFrame()
        
        # 중요: 실제 데이터만 필터링 (학기 요약 정보 등은 제외)
        filtered_rows = []
        for i in range(start_row, len(df)):
            row = df.iloc[i]
            # 학년도가 있고, 이수구분이 있는 행만 선택 (이수구분 목록 확장)
            if (not pd.isna(row.iloc[columns_data['year']]) and 
                not pd.isna(row.iloc[columns_data['course_type']]) and 
                str(row.iloc[columns_data['course_type']]).strip() in 
                ['전선', '전필', '기교', '지교', '핵교', '일교', '일선', '심교', '전공선택', '전공필수', '기초교양', '지정교양', '핵심교양', '일반교양', '일반선택', '심화교양']):
                filtered_rows.append(i)
        
        # 필요한 데이터 추출
        for col_name, col_idx in columns_data.items():
            new_df[col_name] = df.iloc[filtered_rows, col_idx]
        
        # 데이터 정제
        new_df['year'] = pd.to_numeric(new_df['year'], errors='coerce')
        new_df['credits'] = pd.to_numeric(new_df['credits'], errors='coerce')
        
        # 과목명에서 공백 제거
        new_df['course_name'] = new_df['course_name'].astype(str).str.strip()
        
        # 취득학점포기 제외를 위한 추가 열 (있는 경우)
        delete_col = None
        for col_idx in range(df.shape[1]):
            col_values = df.iloc[filtered_rows, col_idx]
            col_values_str = [str(v).strip() for v in col_values if not pd.isna(v)]
            # 취득학점포기 정보가 있는 열 찾기
            if any('취득학점포기' in val for val in col_values_str):
                delete_col = col_idx
                new_df['delete_type'] = df.iloc[filtered_rows, col_idx]
                break
        
        # 다른 방식으로도 취득학점포기 찾아보기
        if delete_col is None:
            # 모든 열을 검색하며 '취득학점포기'가 포함된 행을 찾음
            for i in filtered_rows:
                row = df.iloc[i]
                row_text = ' '.join([str(cell) for cell in row if not pd.isna(cell)])
                if '취득학점포기' in row_text:
                    if 'delete_type' not in new_df:
                        new_df['delete_type'] = 'N'  # 기본값
                    new_df.loc[new_df.index[filtered_rows.index(i)], 'delete_type'] = '취득학점포기'
        
        # 취득학점포기 과목 제외
        original_count = len(new_df)
        if 'delete_type' in new_df.columns:
            new_df = new_df[~new_df['delete_type'].astype(str).str.contains('취득학점포기')].copy()
            excluded_count = original_count - len(new_df)
            print(f"취득학점포기 과목 {excluded_count}개 제외됨")
        
        # F 학점 과목 표시 및 제외
        if 'grade' in new_df.columns:
            # f_grade_count = new_df[new_df['grade'].isin(['F', 'NP'])].shape[0]
            # print(f"F/NP 학점 과목 수: {f_grade_count}")
            
            # F 학점 과목 수 출력
            f_grade_count = new_df[new_df['grade'].isin(['F', 'NP'])].shape[0]
            print(f"F/NP 학점 과목 수: {f_grade_count}")
            
            # # F 학점 과목 제외
            # new_df = new_df[~new_df['grade'].isin(['F', 'NP'])].copy()
            # print(f"F/NP 학점 {f_grade_count}개 과목 제외됨")
        
        # 결측치 제거
        na_count_before = len(new_df)
        new_df = new_df.dropna(subset=['course_name', 'course_type', 'credits']).copy()
        na_count = na_count_before - len(new_df)
        print(f"결측치로 인해 {na_count}개 행 제외됨")
        
        # 디버깅: 전체 학점 합계 출력
        total_credits = new_df['credits'].sum()
        print(f"총 이수학점: {total_credits}")
        
        return new_df
        
    except Exception as e:
        print(f"데이터 정제 중 오류 발생: {str(e)}")
        raise 