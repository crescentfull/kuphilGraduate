import pandas as pd
import logging

logger = logging.getLogger(__name__)

def find_data_start_row(df: pd.DataFrame) -> int:
    """실제 데이터가 시작되는 행을 찾습니다."""
    for idx, row in df.iterrows():
        row_text = ''.join(str(cell) for cell in row if pd.notnull(cell))
        if ('이수구분' in row_text or '과목구분' in row_text) and ('과목' in row_text or '교과목' in row_text):
            return idx
    raise ValueError("성적표 헤더를 찾을 수 없습니다.")

def clean_dataframe(df: pd.DataFrame):
    """성적표 데이터프레임 정제"""
    logger.debug(f"Cleaning DataFrame with shape {df.shape}")
    try:
        columns_data = {
            'year': None,
            'semester': None,
            'course_type': None,
            'course_name': None,
            'credits': None,
            'grade': None
        }

        start_row = 10
        for i in range(5, 20):
            row = df.iloc[i]
            if not pd.isna(row.iloc[1]) and str(row.iloc[1]).isdigit() and '학기' in str(row.iloc[3]):
                start_row = i
                break

        for col_idx in range(df.shape[1]):
            col_values = df.iloc[start_row:start_row+10, col_idx].astype(str)
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

        if None in columns_data.values():
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

        new_df = pd.DataFrame()
        filtered_rows = []
        for i in range(start_row, len(df)):
            row = df.iloc[i]
            if (not pd.isna(row.iloc[columns_data['year']]) and 
                not pd.isna(row.iloc[columns_data['course_type']]) and 
                str(row.iloc[columns_data['course_type']]).strip() in 
                ['전선', '전필', '기교', '지교','지필','다선','다필', '다지', '핵교', '일교', '일선', '심교']):
                filtered_rows.append(i)

        for col_name, col_idx in columns_data.items():
            new_df[col_name] = df.iloc[filtered_rows, col_idx]

        new_df['year'] = pd.to_numeric(new_df['year'], errors='coerce')
        new_df['credits'] = pd.to_numeric(new_df['credits'], errors='coerce')
        new_df['course_name'] = new_df['course_name'].astype(str).str.strip()

        delete_col = None
        for col_idx in range(df.shape[1]):
            col_values_str = [str(v).strip() for v in df.iloc[filtered_rows, col_idx] if not pd.isna(v)]
            if any('취득학점포기' in val for val in col_values_str):
                delete_col = col_idx
                new_df['delete_type'] = df.iloc[filtered_rows, col_idx]
                break

        if delete_col is None:
            for i in filtered_rows:
                row_text = ' '.join([str(cell) for cell in df.iloc[i] if not pd.isna(cell)])
                if '취득학점포기' in row_text:
                    if 'delete_type' not in new_df:
                        new_df['delete_type'] = 'N'
                    new_df.loc[new_df.index[filtered_rows.index(i)], 'delete_type'] = '취득학점포기'

        original_count = len(new_df)
        if 'delete_type' in new_df.columns:
            filtered_df = new_df[~new_df['delete_type'].astype(str).str.contains('취득학점포기')]
            deleted_count = original_count - len(filtered_df)
            logger.debug(f"취득학점포기 과목 삭제: {deleted_count}개")
            new_df = filtered_df.copy()

        if 'grade' in new_df.columns:
            pass

        new_df = new_df.dropna(subset=['course_name', 'course_type', 'credits']).copy()
        return new_df
    except Exception as e:
        logger.exception("Data cleaning error")
        raise 