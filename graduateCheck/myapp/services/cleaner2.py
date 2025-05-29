import pandas as pd
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class ExcelStructureDetector:
    """엑셀 파일의 구조를 자동으로 감지하는 클래스"""
    
    def __init__(self):
        # 컬럼 식별을 위한 키워드들
        self.column_keywords = {
            'year': ['년도', '학년도', '이수년도', '수강년도'],
            'semester': ['학기', '이수학기', '수강학기'],
            'course_type': ['이수구분', '과목구분', '교과구분', '구분', '과목분류'],
            'course_name': ['과목명', '교과목명', '과목', '교과목', '강의명'],
            'credits': ['학점', '이수학점', '취득학점', '단위'],
            'grade': ['성적', '등급', '평점', '학점성적']
        }
        
        # 과목 구분 값들
        self.course_types = [
            '전선', '전필', '기교', '지교', '지필', '다선', '다필', '다지', 
            '핵교', '일교', '일선', '심교', '전공선택', '전공필수', '기초교양',
            '지정교양', '지정교양필수', '다전공선택', '다전공필수', '다전공지교',
            '핵심교양', '일반교양', '일반선택', '심화교양'
        ]
        
        # 성적 값들
        self.grade_values = [
            'A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F', 'P', 'N',
            'A0', 'B0', 'C0', 'D0', 'F0'
        ]

    def detect_structure(self, df: pd.DataFrame):
        """엑셀 파일의 구조를 자동 감지"""
        logger.info("엑셀 파일 구조 감지 시작")
        
        structure = {
            'header_row': None,
            'data_start_row': None,
            'columns': {},
            'format_type': None
        }
        
        # 취득학점확인원 형식인지 확인
        if self._is_credit_confirmation_format(df):
            structure['format_type'] = 'credit_confirmation'
            structure['data_start_row'] = self._find_credit_confirmation_data_start(df)
            logger.info("취득학점확인원 형식으로 감지됨")
            return structure
        
        # 기존 방식으로 처리
        # 1. 헤더 행 찾기
        structure['header_row'] = self._find_header_row(df)
        
        # 2. 데이터 시작 행 찾기
        structure['data_start_row'] = self._find_data_start_row(df, structure['header_row'])
        
        # 3. 컬럼 매핑 찾기
        structure['columns'] = self._find_column_mapping(df, structure['header_row'], structure['data_start_row'])
        
        # 4. 파일 형식 타입 타입 결정
        structure['format_type'] = self._determine_format_type(df, structure)
        
        logger.info(f"감지된 구조: {structure}")
        return structure

    def _is_credit_confirmation_format(self, df: pd.DataFrame):
        """취득학점확인원 형식인지 확인"""
        # 첫 번째 행에 '취득학점 확인원'이 있는지 확인
        if len(df) > 0:
            first_row_text = ' '.join([str(cell) for cell in df.iloc[0] if pd.notnull(cell)])
            if '취득학점' in first_row_text and '확인원' in first_row_text:
                return True
        
        # 과목구분이 행의 시작에 있고, 같은 행에 여러 과목이 있는 패턴 확인
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            row_values = [str(cell).strip() for cell in row if pd.notnull(cell) and str(cell).strip()]
            
            if len(row_values) > 5:  # 충분한 데이터가 있는 행
                # 첫 번째 값이 과목구분이고, 행에 여러 과목 정보가 있는지 확인
                if (row_values[0] in self.course_types or 
                    (len(row_values) > 1 and row_values[1] in self.course_types)):
                    # 학기 패턴 (22/1, 23/2 등) 확인
                    semester_pattern_count = sum(1 for val in row_values if re.match(r'\d{2}/\d', val))
                    if semester_pattern_count >= 2:  # 여러 학기 정보가 있음
                        return True
        
        return False

    def _find_credit_confirmation_data_start(self, df: pd.DataFrame):
        """취득학점확인원에서 데이터 시작 행 찾기"""
        for i in range(len(df)):
            row = df.iloc[i]
            row_values = [str(cell).strip() for cell in row if pd.notnull(cell) and str(cell).strip()]
            
            if len(row_values) > 3:
                # 과목구분이 있고 학기 패턴이 있는 행 찾기
                has_course_type = any(val in self.course_types for val in row_values[:3])
                has_semester = any(re.match(r'\d{2}/\d', val) for val in row_values)
                
                if has_course_type and has_semester:
                    return i
        
        return 3  # 기본값

    def _find_header_row(self, df: pd.DataFrame):
        """헤더 행을 찾습니다"""
        for idx in range(min(20, len(df))):
            row = df.iloc[idx]
            row_text = ' '.join([str(cell) for cell in row if pd.notnull(cell)]).lower()
            
            # 헤더 키워드가 포함된 행 찾기
            header_keywords = ['과목명', '교과목명', '이수구분', '과목구분', '학점', '성적']
            if sum(1 for keyword in header_keywords if keyword in row_text) >= 3:
                return idx
        
        return None

    def _find_data_start_row(self, df: pd.DataFrame, header_row: Optional[int]):
        """실제 데이터가 시작되는 행을 찾습니다"""
        start_search = header_row + 1 if header_row is not None else 0
        
        for idx in range(start_search, min(start_search + 10, len(df))):
            row = df.iloc[idx]
            
            # 과목 구분이 있는 행을 찾기
            for cell in row:
                if pd.notnull(cell) and str(cell).strip() in self.course_types:
                    return idx
        
        # 기본값으로 헤더 다음 행 또는 10행
        return header_row + 1 if header_row is not None else 10

    def _find_column_mapping(self, df: pd.DataFrame, header_row: Optional[int], data_start_row: int):
        """컬럼 매핑을 찾습니다"""
        columns = {}
        
        # 헤더 행이 있는 경우 헤더 기반으로 찾기
        if header_row is not None:
            columns = self._find_columns_by_header(df, header_row)
        
        # 헤더로 찾지 못한 컬럼들은 데이터 패턴으로 찾기
        missing_columns = [col for col, idx in columns.items() if idx is None]
        if missing_columns or not columns:
            pattern_columns = self._find_columns_by_pattern(df, data_start_row)
            for col, idx in pattern_columns.items():
                if col not in columns or columns[col] is None:
                    columns[col] = idx
        
        return columns

    def _find_columns_by_header(self, df: pd.DataFrame, header_row: int):
        """헤더 행을 기반으로 컬럼을 찾습니다"""
        columns = {col: None for col in self.column_keywords.keys()}
        header = df.iloc[header_row]
        
        for col_idx, cell in enumerate(header):
            if pd.notnull(cell):
                cell_text = str(cell).strip()
                
                for col_name, keywords in self.column_keywords.items():
                    if any(keyword in cell_text for keyword in keywords):
                        columns[col_name] = col_idx
                        break
        
        return columns

    def _find_columns_by_pattern(self, df: pd.DataFrame, data_start_row: int):
        """데이터 패턴을 기반으로 컬럼을 찾습니다"""
        columns = {col: None for col in self.column_keywords.keys()}
        
        # 분석할 행 범위 설정
        end_row = min(data_start_row + 20, len(df))
        
        for col_idx in range(df.shape[1]):
            col_data = df.iloc[data_start_row:end_row, col_idx]
            col_values = [str(v).strip() for v in col_data if pd.notnull(v)]
            
            if not col_values:
                continue
            
            # 년도 컬럼 찾기 (4자리 숫자)
            if columns['year'] is None and self._is_year_column(col_values):
                columns['year'] = col_idx
            
            # 학기 컬럼 찾기
            elif columns['semester'] is None and self._is_semester_column(col_values):
                columns['semester'] = col_idx
            
            # 과목구분 컬럼 찾기
            elif columns['course_type'] is None and self._is_course_type_column(col_values):
                columns['course_type'] = col_idx
            
            # 과목명 컬럼 찾기
            elif columns['course_name'] is None and self._is_course_name_column(col_values):
                columns['course_name'] = col_idx
            
            # 학점 컬럼 찾기
            elif columns['credits'] is None and self._is_credits_column(col_values):
                columns['credits'] = col_idx
            
            # 성적 컬럼 찾기
            elif columns['grade'] is None and self._is_grade_column(col_values):
                columns['grade'] = col_idx
        
        return columns

    def _is_year_column(self, values: List[str]):
        """년도 컬럼인지 확인"""
        year_count = sum(1 for v in values if re.match(r'^20\d{2}$', v))
        return year_count > len(values) * 0.5

    def _is_semester_column(self, values: List[str]):
        """학기 컬럼인지 확인"""
        semester_count = sum(1 for v in values if '학기' in v or v in ['1', '2', '여름', '겨울'])
        return semester_count > len(values) * 0.5

    def _is_course_type_column(self, values: List[str]):
        """과목구분 컬럼인지 확인"""
        type_count = sum(1 for v in values if v in self.course_types)
        return type_count > len(values) * 0.3

    def _is_course_name_column(self, values: List[str]):
        """과목명 컬럼인지 확인"""
        # 한글이 포함되고 길이가 2자 이상인 값들
        name_count = sum(1 for v in values if len(v) >= 2 and re.search(r'[가-힣]', v))
        return name_count > len(values) * 0.5

    def _is_credits_column(self, values: List[str]):
        """학점 컬럼인지 확인"""
        numeric_count = sum(1 for v in values if re.match(r'^\d+(\.\d+)?$', v))
        return numeric_count > len(values) * 0.5

    def _is_grade_column(self, values: List[str]):
        """성적 컬럼인지 확인"""
        grade_count = sum(1 for v in values if v in self.grade_values)
        return grade_count > len(values) * 0.3

    def _determine_format_type(self, df: pd.DataFrame, structure: Dict):
        """파일 형식 타입을 결정합니다"""
        if structure['header_row'] is not None:
            return 'header_based'
        else:
            return 'pattern_based'


class FlexibleCleaner:
    """유연한 데이터 정제기"""
    
    def __init__(self):
        self.detector = ExcelStructureDetector()
        
        # 과목명 매핑 (기존과 동일)
        self.course_name_mapping = {
            '철학의이해': '철학산책',
            '서양고대철학': '서양고중세철학',
            '현대철학': '서양현대철학',
            '유가철학': '중국유학'
        }
        
        # 과목 구분 매핑 (기존과 동일)
        self.course_type_mapping = {
            '기교': '기초교양',
            '핵교': '핵심교양',
            '일교': '일반교양',
            '지교': '지정교양',
            '지필': '지정교양필수',
            '전선': '전공선택',
            '전필': '전공필수',
            '일선': '일반선택',
            '심교': '심화교양',
            '다선': '다전공선택',
            '다지': '다전공지교',
            '다필': '다전공필수',
        }

    def clean_dataframe(self, df: pd.DataFrame):
        """새로운 방식으로 데이터프레임을 정제합니다"""
        logger.info(f"FlexibleCleaner로 데이터프레임 정제 시작 - 크기: {df.shape}")
        
        try:
            # 1. 구조 감지
            structure = self.detector.detect_structure(df)
            
            # 2. 형식에 따른 처리
            if structure['format_type'] == 'credit_confirmation':
                cleaned_df = self._process_credit_confirmation_format(df, structure)
            else:
                if not structure['columns'] or None in structure['columns'].values():
                    raise ValueError("필수 컬럼을 찾을 수 없습니다. 파일 형식을 확인해주세요.")
                
                # 기존 방식으로 처리
                cleaned_df = self._extract_data(df, structure)
                cleaned_df = self._clean_and_transform(cleaned_df)
                cleaned_df = self._filter_valid_courses(cleaned_df)
            
            logger.info(f"정제 완료 - 최종 크기: {cleaned_df.shape}")
            return cleaned_df
            
        except Exception as e:
            logger.exception("FlexibleCleaner 정제 중 오류 발생")
            raise ValueError(f"데이터 정제 실패: {str(e)}")

    def _process_credit_confirmation_format(self, df: pd.DataFrame, structure: Dict):
        """취득학점확인원 형식 처리"""
        courses = []
        data_start = structure['data_start_row']
        current_course_type = None  # 현재 과목구분 추적
        
        for idx in range(data_start, len(df)):
            row = df.iloc[idx]
            row_values = [str(cell).strip() for cell in row if pd.notnull(cell) and str(cell).strip()]
            
            if len(row_values) < 3:
                continue
            
            # 과목구분 찾기 - 첫 번째나 두 번째 값에서
            course_type = None
            for i in range(min(3, len(row_values))):
                if row_values[i] in self.detector.course_types:
                    course_type = row_values[i]
                    current_course_type = course_type  # 현재 과목구분 업데이트
                    break
            
            # 과목구분이 없으면 이전 과목구분 사용
            if not course_type and current_course_type:
                course_type = current_course_type
            
            if not course_type:
                continue
            
            # 해당 행에서 과목 정보 추출
            extracted_courses = self._extract_courses_from_row(row_values, course_type)
            courses.extend(extracted_courses)
        
        if not courses:
            raise ValueError("유효한 성적 데이터를 찾을 수 없습니다.")
        
        # DataFrame 생성
        result_df = pd.DataFrame(courses)
        
        # 데이터 정제 및 변환
        result_df = self._clean_and_transform(result_df)
        result_df = self._filter_valid_courses(result_df)
        
        logger.info(f"취득학점확인원에서 {len(result_df)}개 과목 추출")
        return result_df

    def _extract_courses_from_row(self, row_values: List[str], course_type: str):
        """한 행에서 여러 과목 추출"""
        courses = []
        i = 0
        
        # 과목구분이 있는 경우 과목구분과 총학점 정보 스킵
        has_course_type_in_row = any(val in self.detector.course_types for val in row_values[:3])
        
        if has_course_type_in_row:
            # 과목구분과 총학점 정보 스킵
            while i < len(row_values):
                if row_values[i] in self.detector.course_types:
                    i += 1
                    # 총학점 정보 스킵 (숫자.0 형태)
                    while i < len(row_values) and (
                        re.match(r'^\d+\.\d+$', row_values[i]) or 
                        re.match(r'^\(\d+\.\d+\)$', row_values[i])
                    ):
                        i += 1
                    break
                i += 1
        
        # 과목 추출 시작
        while i < len(row_values):
            # 학기 패턴을 찾으면 과목 시작 (22/2, 22/2 1, (계)24/1 3 형태)
            if re.match(r'^(\([^)]+\))?\d{2}/\d(\s+\d)?$', row_values[i]):
                course_info = self._extract_single_course(row_values, i)
                if course_info:
                    course_info['course_type'] = course_type
                    courses.append(course_info)
                    i = course_info['next_index']
                else:
                    i += 1
            else:
                i += 1
        
        return courses

    def _extract_single_course(self, row_values: List[str], start_idx: int):
        """단일 과목 정보 추출"""
        if start_idx >= len(row_values):
            return None
        
        course_info = {}
        i = start_idx
        
        # 학기 정보 찾기 (22/1, 23/2, 22/2 1, (계)24/1 3 형태)
        semester_match = re.match(r'^(\([^)]+\))?(\d{2})/(\d)(\s+\d)?$', row_values[i])
        if semester_match:
            year = 2000 + int(semester_match.group(2))
            semester_num = semester_match.group(3)
            course_info['year'] = year
            course_info['semester'] = f"{semester_num}학기"
            i += 1
        else:
            # 학기 정보가 없으면 기본값
            course_info['year'] = 2024
            course_info['semester'] = '1학기'
        
        # 과목코드 스킵 (BAGA49118 형태 또는 숫자가 포함된 코드)
        if i < len(row_values) and (
            re.match(r'^[A-Z]{4}\d+', row_values[i]) or 
            re.match(r'^[A-Z]+\d+', row_values[i]) or
            '(' in row_values[i]  # BKSA56558(SW) 같은 형태
        ):
            i += 1
        
        # 과목명 찾기 - 한글이 포함되고 길이가 2자 이상
        course_name_found = False
        while i < len(row_values) and not course_name_found:
            current_value = row_values[i]
            
            # 과목명 조건: 한글 포함, 2자 이상, 숫자나 성적이 아님
            if (len(current_value) >= 2 and 
                re.search(r'[가-힣]', current_value) and
                not re.match(r'^\d+(\.\d+)?$', current_value) and  # 숫자가 아님
                current_value not in self.detector.grade_values):  # 성적이 아님
                
                course_info['course_name'] = current_value
                course_name_found = True
                i += 1
                break
            i += 1
        
        if not course_name_found:
            return None  # 과목명이 없으면 유효하지 않은 과목
        
        # 학점 찾기 - 과목명 다음에 오는 숫자
        credits_found = False
        while i < len(row_values) and not credits_found:
            if re.match(r'^\d+(\.\d+)?$', row_values[i]):
                try:
                    credits = float(row_values[i])
                    if 0.5 <= credits <= 6.0:  # 합리적인 학점 범위
                        course_info['credits'] = int(credits)  # int로 변환
                        credits_found = True
                        i += 1
                        break
                except ValueError:
                    pass
            i += 1
        
        if not credits_found:
            course_info['credits'] = 3  # 기본값도 int로
        
        # 성적 찾기 - 학점 다음에 오는 성적
        grade_found = False
        while i < len(row_values) and not grade_found:
            if row_values[i] in self.detector.grade_values:
                course_info['grade'] = row_values[i]
                grade_found = True
                i += 1
                break
            # 다음 학기 패턴이 나오면 성적 찾기 중단
            if re.match(r'^(\([^)]+\))?\d{2}/\d(\s+\d)?$', row_values[i]):
                break
            i += 1
        
        if not grade_found:
            course_info['grade'] = 'P'  # 기본값
        
        course_info['next_index'] = i
        return course_info

    def _extract_data(self, df: pd.DataFrame, structure: Dict):
        """구조 정보를 바탕으로 데이터를 추출합니다"""
        columns = structure['columns']
        data_start = structure['data_start_row']
        
        # 유효한 데이터 행 찾기
        valid_rows = []
        for idx in range(data_start, len(df)):
            row = df.iloc[idx]
            
            # 과목구분이 유효한 값인지 확인
            course_type_col = columns.get('course_type')
            if course_type_col is not None:
                course_type = str(row.iloc[course_type_col]).strip()
                if course_type in self.detector.course_types:
                    valid_rows.append(idx)
        
        if not valid_rows:
            raise ValueError("유효한 성적 데이터를 찾을 수 없습니다.")
        
        # 데이터 추출
        result_data = {}
        for col_name, col_idx in columns.items():
            if col_idx is not None:
                result_data[col_name] = df.iloc[valid_rows, col_idx].values
            else:
                # 기본값 설정
                if col_name == 'year':
                    result_data[col_name] = [2024] * len(valid_rows)
                elif col_name == 'semester':
                    result_data[col_name] = ['1학기'] * len(valid_rows)
                else:
                    result_data[col_name] = [None] * len(valid_rows)
        
        return pd.DataFrame(result_data)

    def _clean_and_transform(self, df: pd.DataFrame):
        """데이터 정제 및 변환"""
        df = df.copy()
        
        # 문자열 정제
        for col in ['course_name', 'course_type', 'grade']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # 숫자 변환
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        if 'credits' in df.columns:
            df['credits'] = pd.to_numeric(df['credits'], errors='coerce').astype('Int64')
        
        # 과목명 매핑 적용
        if 'course_name' in df.columns:
            df['course_name'] = df['course_name'].str.replace(' ', '')
            for old_name, new_name in self.course_name_mapping.items():
                df.loc[df['course_name'] == old_name, 'course_name'] = new_name
        
        # 과목구분 매핑 적용
        if 'course_type' in df.columns:
            for old_type, new_type in self.course_type_mapping.items():
                df.loc[df['course_type'] == old_type, 'course_type'] = new_type
        
        return df

    def _filter_valid_courses(self, df: pd.DataFrame):
        """유효한 과목만 필터링"""
        # 필수 컬럼이 있는 행만 유지
        required_cols = ['course_name', 'course_type', 'credits']
        existing_cols = [col for col in required_cols if col in df.columns]
        
        if existing_cols:
            df = df.dropna(subset=existing_cols)
        
        # 학점이 0보다 큰 과목만 유지
        if 'credits' in df.columns:
            df = df[df['credits'] > 0]
        
        # 과목명이 의미있는 값인 과목만 유지
        if 'course_name' in df.columns:
            df = df[df['course_name'].str.len() >= 2]
            df = df[~df['course_name'].isin(['nan', 'None', ''])]
        
        return df.reset_index(drop=True)


def clean_dataframe_v2(df: pd.DataFrame):
    """새로운 정제 함수 - 기존 함수와 호환성 유지"""
    cleaner = FlexibleCleaner()
    return cleaner.clean_dataframe(df)


# 기존 함수와의 호환성을 위한 별칭
clean_dataframe_flexible = clean_dataframe_v2 