"""
로어북 API
SYNK 창작자 스튜디오 - 로어북 CRUD 및 순서 변경
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.creator_models import (
    LorebookEntryCreate, LorebookEntryUpdate, LorebookEntryResponse,
    LorebookReorderRequest
)
from db.supabase_db import (
    create_lorebook_entry, get_lorebook_entry, get_lorebook_entries_by_work,
    update_lorebook_entry, delete_lorebook_entry, reorder_lorebook_entries
)
from api.auth import get_current_user, UserInfo
from db.supabase_db import get_work

router = APIRouter(prefix="/api/creator/works/{work_id}/lorebook", tags=["creator_lorebook"])


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


@router.post("", response_model=LorebookEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_lorebook_entry_endpoint(
    work_id: str,
    entry_data: LorebookEntryCreate,
    current_user: UserInfo = Depends(get_current_user)
):
    """로어 추가"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        entry = create_lorebook_entry(work_id, entry_data)
        return entry
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로어 추가 실패: {str(e)}"
        )


@router.get("", response_model=List[LorebookEntryResponse])
async def get_lorebook_entries_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """로어 목록 조회"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        entries = get_lorebook_entries_by_work(work_id)
        return entries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로어 목록 조회 실패: {str(e)}"
        )


@router.put("/{entry_id}", response_model=LorebookEntryResponse)
async def update_lorebook_entry_endpoint(
    work_id: str,
    entry_id: str,
    entry_data: LorebookEntryUpdate,
    current_user: UserInfo = Depends(get_current_user)
):
    """로어 수정"""
    verify_work_ownership(work_id, current_user.user_id)
    
    entry = get_lorebook_entry(entry_id)
    if not entry or entry.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="로어를 찾을 수 없습니다."
        )
    
    try:
        updated_entry = update_lorebook_entry(entry_id, entry_data)
        if not updated_entry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="로어 수정 실패"
            )
        return updated_entry
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로어 수정 실패: {str(e)}"
        )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lorebook_entry_endpoint(
    work_id: str,
    entry_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """로어 삭제"""
    verify_work_ownership(work_id, current_user.user_id)
    
    entry = get_lorebook_entry(entry_id)
    if not entry or entry.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="로어를 찾을 수 없습니다."
        )
    
    try:
        success = delete_lorebook_entry(entry_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="로어 삭제 실패"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로어 삭제 실패: {str(e)}"
        )


@router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_lorebook_entries_endpoint(
    work_id: str,
    request: LorebookReorderRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """로어 순서 변경"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        success = reorder_lorebook_entries(work_id, request.entry_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="로어 순서 변경 실패"
            )
        return {"message": "로어 순서가 변경되었습니다."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로어 순서 변경 실패: {str(e)}"
        )
