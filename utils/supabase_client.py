"""
Supabase 클라이언트 설정
SYNK 창작자 스튜디오 - Supabase 연동
"""
import os
from supabase import create_client, Client
from typing import Optional
from utils.config import load_env

# 환경 변수 로드
load_env()

# Supabase 설정
# 사용자가 SUPERBASE로 오타했지만 .env 파일과 일치하도록 그대로 사용
SUPABASE_URL = os.getenv("SUPERBASE_URL")
SUPABASE_KEY = os.getenv("SUPERBASE_API_KEY")
SUPABASE_SECRET_KEY = os.getenv("SUPERBASE_SECRET_KEY")

# Supabase 클라이언트 인스턴스
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 가져오기 (싱글톤)
    
    Returns:
        Supabase 클라이언트 인스턴스
        
    Raises:
        ValueError: Supabase 설정이 없을 경우
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Supabase 설정이 없습니다. .env 파일에 다음을 설정하세요:\n"
                "SUPERBASE_URL=your_supabase_url\n"
                "SUPERBASE_API_KEY=your_api_key\n"
                "SUPERBASE_SECRET_KEY=your_secret_key"
            )
        
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    return _supabase_client


def get_supabase_admin_client() -> Client:
    """
    Supabase Admin 클라이언트 가져오기 (서비스 역할)
    
    Returns:
        Supabase Admin 클라이언트 인스턴스
        
    Raises:
        ValueError: Supabase 설정이 없을 경우
    """
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise ValueError(
            "Supabase Admin 설정이 없습니다. .env 파일에 다음을 설정하세요:\n"
            "SUPERBASE_URL=your_supabase_url\n"
            "SUPERBASE_SECRET_KEY=your_secret_key"
        )
    
    # Admin 클라이언트는 서비스 역할 키 사용
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
