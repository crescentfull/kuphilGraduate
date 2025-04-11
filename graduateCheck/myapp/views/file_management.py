from django.shortcuts import render
import os
from django.conf import settings

import logging

# 로거 생성
logger = logging.getLogger('myapp')

def cleanup_files(request):
    """미디어 디렉토리의 모든 파일 삭제"""
    cleaned_files = 0
    
    try:
        # 미디어 디렉토리 경로
        media_dir = settings.MEDIA_ROOT
        
        if os.path.exists(media_dir):
            # 모든 파일 삭제 (하위 디렉토리는 유지)
            for item in os.listdir(media_dir):
                item_path = os.path.join(media_dir, item)
                
                # 파일인 경우 삭제
                if os.path.isfile(item_path):
                    try:
                        os.unlink(item_path)
                        cleaned_files += 1
                        logger.info(f"파일 삭제: {item_path}")
                    except Exception as e:
                        logger.error(f"파일 '{item_path}' 삭제 중 오류: {str(e)}")
                
                # 디렉토리인 경우 내부 파일만 삭제 (디렉토리 구조는 유지)
                elif os.path.isdir(item_path):
                    try:
                        for file_name in os.listdir(item_path):
                            file_path = os.path.join(item_path, file_name)
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                                cleaned_files += 1
                                logger.info(f"파일 삭제: {file_path}")
                    except Exception as e:
                        logger.error(f"디렉토리 '{item_path}' 내 파일 삭제 중 오류: {str(e)}")
            
            logger.info(f"총 {cleaned_files}개 파일이 삭제되었습니다.")
        else:
            logger.warning(f"미디어 디렉토리가 존재하지 않습니다: {media_dir}")
        
        # 결과 페이지 렌더링
        return render(request, 'cleanup.html', {'cleaned_files': cleaned_files})
    
    except Exception as e:
        logger.error(f"Cleanup 작업 중 오류 발생: {str(e)}")
        return render(request, 'error.html', {'error': str(e)})