"""
작품 API
SYNK 창작자 스튜디오 - 작품 CRUD 및 발행
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.creator_models import WorkCreate, WorkUpdate, WorkResponse
from db.supabase_db import (
    create_work, get_work, get_works_by_creator,
    update_work, delete_work, publish_work, unpublish_work
)
from api.auth import get_current_user, UserInfo

router = APIRouter(prefix="/api/creator/works", tags=["creator_works"])


@router.post("", response_model=WorkResponse, status_code=status.HTTP_201_CREATED)
async def create_work_endpoint(
    work_data: WorkCreate,
    current_user: UserInfo = Depends(get_current_user)
):
    """작품 생성"""
    try:
        work = create_work(current_user.user_id, work_data)
        return work
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작품 생성 실패: {str(e)}"
        )


@router.get("", response_model=List[WorkResponse])
async def get_works_endpoint(
    current_user: UserInfo = Depends(get_current_user)
):
    """내 작품 목록 조회"""
    try:
        works = get_works_by_creator(current_user.user_id)
        return works
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작품 목록 조회 실패: {str(e)}"
        )


@router.get("/{work_id}", response_model=WorkResponse)
async def get_work_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """작품 상세 조회"""
    work = get_work(work_id)
    
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다."
        )
    
    # 권한 확인 (자신의 작품이거나 공개된 작품만)
    if work.creator_id != current_user.user_id and work.visibility != "public":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작품에 접근할 권한이 없습니다."
        )
    
    return work


@router.put("/{work_id}", response_model=WorkResponse)
async def update_work_endpoint(
    work_id: str,
    work_data: WorkUpdate,
    current_user: UserInfo = Depends(get_current_user)
):
    """작품 수정"""
    # 권한 확인
    work = get_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다."
        )
    
    if work.creator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작품을 수정할 권한이 없습니다."
        )
    
    try:
        updated_work = update_work(work_id, work_data)
        if not updated_work:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="작품 수정 실패"
            )
        return updated_work
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작품 수정 실패: {str(e)}"
        )


@router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """작품 삭제"""
    # 권한 확인
    work = get_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다."
        )
    
    if work.creator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작품을 삭제할 권한이 없습니다."
        )
    
    try:
        success = delete_work(work_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="작품 삭제 실패"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작품 삭제 실패: {str(e)}"
        )


@router.post("/{work_id}/publish", response_model=WorkResponse)
async def publish_work_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """작품 발행"""
    # 권한 확인
    work = get_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다."
        )
    
    if work.creator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작품을 발행할 권한이 없습니다."
        )
    
    try:
        published_work = publish_work(work_id)
        if not published_work:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="작품 발행 실패"
            )
        return published_work
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작품 발행 실패: {str(e)}"
        )


@router.post("/{work_id}/unpublish", response_model=WorkResponse)
async def unpublish_work_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """작품 비공개"""
    # 권한 확인
    work = get_work(work_id)
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다."
        )
    
    if work.creator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="작품을 비공개할 권한이 없습니다."
        )
    
    try:
        unpublished_work = unpublish_work(work_id)
        if not unpublished_work:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="작품 비공개 실패"
            )
        return unpublished_work
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작품 비공개 실패: {str(e)}"
        )
