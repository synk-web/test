"""
오프닝 API
SYNK 창작자 스튜디오 - 오프닝 CRUD 및 기본 오프닝 설정
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.creator_models import OpeningCreate, OpeningUpdate, OpeningResponse
from db.supabase_db import (
    create_opening, get_opening, get_openings_by_work,
    update_opening, delete_opening, set_default_opening
)
from api.auth import get_current_user, UserInfo
from db.supabase_db import get_work

router = APIRouter(prefix="/api/creator/works/{work_id}/openings", tags=["creator_openings"])


def verify_work_ownership(work_id: str, user_id: str) -> None:
    """작품 소유권 확인"""
    work = get_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다."
        )
    
    if work.creator_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작품에 접근할 권한이 없습니다."
        )


@router.post("", response_model=OpeningResponse, status_code=status.HTTP_201_CREATED)
async def create_opening_endpoint(
    work_id: str,
    opening_data: OpeningCreate,
    current_user: UserInfo = Depends(get_current_user)
):
    """오프닝 추가"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        opening = create_opening(work_id, opening_data)
        return opening
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오프닝 추가 실패: {str(e)}"
        )


@router.get("", response_model=List[OpeningResponse])
async def get_openings_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """오프닝 목록 조회"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        openings = get_openings_by_work(work_id)
        return openings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오프닝 목록 조회 실패: {str(e)}"
        )


@router.put("/{opening_id}", response_model=OpeningResponse)
async def update_opening_endpoint(
    work_id: str,
    opening_id: str,
    opening_data: OpeningUpdate,
    current_user: UserInfo = Depends(get_current_user)
):
    """오프닝 수정"""
    verify_work_ownership(work_id, current_user.user_id)
    
    opening = get_opening(opening_id)
    if not opening or opening.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오프닝을 찾을 수 없습니다."
        )
    
    try:
        updated_opening = update_opening(opening_id, opening_data)
        if not updated_opening:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="오프닝 수정 실패"
            )
        return updated_opening
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오프닝 수정 실패: {str(e)}"
        )


@router.delete("/{opening_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opening_endpoint(
    work_id: str,
    opening_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """오프닝 삭제"""
    verify_work_ownership(work_id, current_user.user_id)
    
    opening = get_opening(opening_id)
    if not opening or opening.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오프닝을 찾을 수 없습니다."
        )
    
    try:
        success = delete_opening(opening_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="오프닝 삭제 실패"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"오프닝 삭제 실패: {str(e)}"
        )


@router.put("/{opening_id}/set-default", response_model=OpeningResponse)
async def set_default_opening_endpoint(
    work_id: str,
    opening_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """기본 오프닝 설정"""
    verify_work_ownership(work_id, current_user.user_id)
    
    opening = get_opening(opening_id)
    if not opening or opening.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오프닝을 찾을 수 없습니다."
        )
    
    try:
        default_opening = set_default_opening(work_id, opening_id)
        if not default_opening:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="기본 오프닝 설정 실패"
            )
        return default_opening
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기본 오프닝 설정 실패: {str(e)}"
        )
