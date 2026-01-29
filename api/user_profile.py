"""
유저 프로필 API
SYNK MVP - 유저(주인공) 프로필 관리
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from db.character_db import get_db
from db.user_profile_db import get_user_profile, create_user_profile, update_user_profile
from models.user_profile import UserProfile

router = APIRouter(prefix="/api/user/profile", tags=["user_profile"])


class UserProfileUpdateRequest(BaseModel):
    """유저 프로필 수정 요청"""
    nickname: Optional[str] = None
    gender: Optional[str] = None


class UserProfileResponse(BaseModel):
    """유저 프로필 응답"""
    success: bool
    profile: Optional[dict] = None


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """유저 프로필 조회"""
    profile = get_user_profile(user_id, db)
    
    if not profile:
        # 없으면 생성
        profile = create_user_profile(user_id, db)
    
    return UserProfileResponse(
        success=True,
        profile=profile.dict()
    )


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_profile(
    user_id: str,
    request: UserProfileUpdateRequest,
    db: Session = Depends(get_db)
):
    """유저 프로필 수동 업데이트"""
    profile = get_user_profile(user_id, db)
    
    if not profile:
        profile = create_user_profile(user_id, db)
    
    # 업데이트
    if request.nickname is not None:
        profile.nickname = request.nickname
    if request.gender is not None:
        profile.gender = request.gender
    
    updated_profile = update_user_profile(profile, db)
    
    return UserProfileResponse(
        success=True,
        profile=updated_profile.dict()
    )
