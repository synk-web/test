"""
인증 API
SYNK 창작자 스튜디오 - 구글 로그인 및 인증
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from supabase import Client
from utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class GoogleAuthRequest(BaseModel):
    """구글 로그인 요청"""
    id_token: str  # Google ID Token


class AuthResponse(BaseModel):
    """인증 응답"""
    access_token: str
    refresh_token: Optional[str] = None
    user_id: str
    email: Optional[str] = None


class UserInfo(BaseModel):
    """사용자 정보"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """
    현재 사용자 가져오기 (의존성)
    
    Args:
        credentials: HTTP Bearer 토큰
        
    Returns:
        UserInfo: 사용자 정보
        
    Raises:
        HTTPException: 인증 실패 시
    """
    supabase = get_supabase_client()
    
    try:
        # Supabase에서 토큰 검증
        # Supabase Python 클라이언트는 set_session으로 토큰 설정 후 get_user 호출
        session = supabase.auth.set_session(access_token=credentials.credentials, refresh_token="")
        user_response = supabase.auth.get_user()
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 토큰이 유효하지 않습니다."
            )
        
        user = user_response.user
        
        return UserInfo(
            user_id=user.id,
            email=user.email,
            name=user.user_metadata.get("name") if user.user_metadata else None,
            avatar_url=user.user_metadata.get("avatar_url") if user.user_metadata else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"인증 실패: {str(e)}"
        )


@router.post("/google", response_model=AuthResponse)
async def google_login(request: GoogleAuthRequest):
    """
    구글 로그인
    
    Google ID Token을 받아서 Supabase 인증 처리
    """
    supabase = get_supabase_client()
    
    try:
        # Google ID Token으로 Supabase 인증
        # Supabase Python 클라이언트는 sign_in_with_id_token 대신 sign_in_with_oauth_token 사용
        response = supabase.auth.sign_in_with_oauth_token({
            "provider": "google",
            "access_token": request.id_token,
            "id_token": request.id_token
        })
        
        # 또는 직접 ID Token 검증
        # Supabase는 OAuth2를 사용하므로, 클라이언트에서 직접 처리하는 것이 더 나을 수 있음
        # 여기서는 간단히 토큰을 받아서 검증만 수행
        
        # 실제 구현에서는 Supabase의 OAuth 설정이 필요함
        # 임시로 토큰을 그대로 반환 (프론트엔드에서 Supabase 클라이언트로 직접 처리 권장)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="구글 로그인은 프론트엔드에서 Supabase 클라이언트를 사용하여 처리하세요."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"구글 로그인 실패: {str(e)}"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """
    토큰 갱신
    """
    supabase = get_supabase_client()
    
    try:
        response = supabase.auth.refresh_session(refresh_token)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰 갱신 실패"
            )
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"토큰 갱신 실패: {str(e)}"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: UserInfo = Depends(get_current_user)):
    """
    현재 사용자 정보 조회
    """
    return current_user


@router.post("/logout")
async def logout(current_user: UserInfo = Depends(get_current_user)):
    """
    로그아웃
    """
    supabase = get_supabase_client()
    
    try:
        supabase.auth.sign_out()
        return {"message": "로그아웃되었습니다."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그아웃 실패: {str(e)}"
        )
