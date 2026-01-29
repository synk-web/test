"""
환경 설정 유틸리티
공통 환경 변수 로드 및 설정
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_env(project_root: str = None) -> None:
    """
    .env 파일 로드
    
    최적화 전 방식과 동일하게 구현:
    - api/chat_multi.py에서 사용하던 방식: os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    Args:
        project_root: 프로젝트 루트 경로 (None이면 자동 감지)
    """
    if project_root is None:
        # 최적화 전 방식과 동일: 현재 파일 기준으로 프로젝트 루트 찾기
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
    
    env_path = Path(project_root) / '.env'
    
    # .env 파일 존재 확인
    if not env_path.exists():
        print(f"⚠️ 경고: .env 파일을 찾을 수 없습니다: {env_path}")
        return
    
    # 최적화 전 방식과 완전히 동일: override 없이 로드
    # 최적화 전: load_dotenv(dotenv_path=env_path) - override 파라미터 없음
    result = load_dotenv(dotenv_path=str(env_path))
    
    # 최적화 전에는 로드 결과를 확인하지 않았으므로 여기서도 조용히 처리
    # (이미 환경 변수가 설정되어 있으면 load_dotenv는 False를 반환하지만 정상)


def get_gemini_api_key() -> str:
    """
    Gemini API 키 가져오기
    
    Returns:
        API 키 문자열 (없으면 None)
    """
    return os.getenv("GEMINI_API_KEY")


def get_database_url() -> str:
    """
    데이터베이스 URL 가져오기
    
    Returns:
        데이터베이스 URL
    """
    return os.getenv("DATABASE_URL", "sqlite:///./synk_mvp.db")


def get_supabase_url() -> str:
    """
    Supabase URL 가져오기
    
    Returns:
        Supabase URL
    """
    return os.getenv("SUPERBASE_URL")  # 사용자 오타 반영


def get_supabase_api_key() -> str:
    """
    Supabase API Key 가져오기
    
    Returns:
        Supabase API Key
    """
    return os.getenv("SUPERBASE_API_KEY")  # 사용자 오타 반영


def get_supabase_secret_key() -> str:
    """
    Supabase Secret Key 가져오기
    
    Returns:
        Supabase Secret Key
    """
    return os.getenv("SUPERBASE_SECRET_KEY")  # 사용자 오타 반영
