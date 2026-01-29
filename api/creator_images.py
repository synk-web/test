"""
이미지 갤러리 API
SYNK 창작자 스튜디오 - 이미지 CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from models.creator_models import GalleryImageCreate, GalleryImageUpdate, GalleryImageResponse
from db.supabase_db import (
    create_gallery_image, get_gallery_image, get_gallery_images_by_work,
    update_gallery_image, delete_gallery_image
)
from api.auth import get_current_user, UserInfo
from db.supabase_db import get_work

router = APIRouter(prefix="/api/creator/works/{work_id}/images", tags=["creator_images"])


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


@router.post("", response_model=GalleryImageResponse, status_code=status.HTTP_201_CREATED)
async def create_image_endpoint(
    work_id: str,
    image_data: GalleryImageCreate,
    current_user: UserInfo = Depends(get_current_user)
):
    """이미지 업로드"""
    verify_work_ownership(work_id, current_user.user_id)
    
    # 키워드 형식 검증
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', image_data.keyword):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="키워드는 영문, 숫자, 언더바(_)만 사용 가능합니다."
        )
    
    try:
        image = create_gallery_image(work_id, image_data)
        return image
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 생성 실패: {str(e)}"
        )


@router.get("", response_model=List[GalleryImageResponse])
async def get_images_endpoint(
    work_id: str,
    character_name: Optional[str] = Query(None, description="캐릭터 이름 필터"),
    current_user: UserInfo = Depends(get_current_user)
):
    """이미지 목록 조회"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        images = get_gallery_images_by_work(work_id, character_name)
        return images
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 목록 조회 실패: {str(e)}"
        )


@router.get("/{image_id}", response_model=GalleryImageResponse)
async def get_image_endpoint(
    work_id: str,
    image_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """이미지 상세 조회"""
    verify_work_ownership(work_id, current_user.user_id)
    
    image = get_gallery_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지를 찾을 수 없습니다."
        )
    
    if image.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지가 해당 작품에 속하지 않습니다."
        )
    
    return image


@router.put("/{image_id}", response_model=GalleryImageResponse)
async def update_image_endpoint(
    work_id: str,
    image_id: str,
    image_data: GalleryImageUpdate,
    current_user: UserInfo = Depends(get_current_user)
):
    """이미지 수정"""
    verify_work_ownership(work_id, current_user.user_id)
    
    image = get_gallery_image(image_id)
    if not image or image.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지를 찾을 수 없습니다."
        )
    
    # 키워드 형식 검증
    if image_data.keyword:
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', image_data.keyword):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="키워드는 영문, 숫자, 언더바(_)만 사용 가능합니다."
            )
    
    try:
        updated_image = update_gallery_image(image_id, image_data)
        if not updated_image:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이미지 수정 실패"
            )
        return updated_image
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 수정 실패: {str(e)}"
        )


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_endpoint(
    work_id: str,
    image_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """이미지 삭제"""
    verify_work_ownership(work_id, current_user.user_id)
    
    image = get_gallery_image(image_id)
    if not image or image.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이미지를 찾을 수 없습니다."
        )
    
    try:
        success = delete_gallery_image(image_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이미지 삭제 실패"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 삭제 실패: {str(e)}"
        )
