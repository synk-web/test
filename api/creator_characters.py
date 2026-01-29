"""
캐릭터 API
SYNK 창작자 스튜디오 - 캐릭터 CRUD 및 AI 생성
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.creator_models import (
    CharacterCreate, CharacterUpdate, CharacterResponse,
    CharacterGenerateRequest
)
from db.supabase_db import (
    create_character, get_character, get_characters_by_work,
    update_character, delete_character
)
from api.auth import get_current_user, UserInfo
from db.supabase_db import get_work
from utils.gemini_client import GeminiClient

router = APIRouter(prefix="/api/creator/works/{work_id}/characters", tags=["creator_characters"])


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


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character_endpoint(
    work_id: str,
    character_data: CharacterCreate,
    current_user: UserInfo = Depends(get_current_user)
):
    """캐릭터 추가"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        character = create_character(work_id, character_data)
        return character
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐릭터 생성 실패: {str(e)}"
        )


@router.get("", response_model=List[CharacterResponse])
async def get_characters_endpoint(
    work_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """캐릭터 목록 조회"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        characters = get_characters_by_work(work_id)
        return characters
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐릭터 목록 조회 실패: {str(e)}"
        )


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character_endpoint(
    work_id: str,
    character_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """캐릭터 상세 조회"""
    verify_work_ownership(work_id, current_user.user_id)
    
    character = get_character(character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캐릭터를 찾을 수 없습니다."
        )
    
    if character.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="캐릭터가 해당 작품에 속하지 않습니다."
        )
    
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character_endpoint(
    work_id: str,
    character_id: str,
    character_data: CharacterUpdate,
    current_user: UserInfo = Depends(get_current_user)
):
    """캐릭터 수정"""
    verify_work_ownership(work_id, current_user.user_id)
    
    character = get_character(character_id)
    if not character or character.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캐릭터를 찾을 수 없습니다."
        )
    
    try:
        updated_character = update_character(character_id, character_data)
        if not updated_character:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="캐릭터 수정 실패"
            )
        return updated_character
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐릭터 수정 실패: {str(e)}"
        )


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_endpoint(
    work_id: str,
    character_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """캐릭터 삭제"""
    verify_work_ownership(work_id, current_user.user_id)
    
    character = get_character(character_id)
    if not character or character.work_id != work_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캐릭터를 찾을 수 없습니다."
        )
    
    try:
        success = delete_character(character_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="캐릭터 삭제 실패"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐릭터 삭제 실패: {str(e)}"
        )


@router.post("/generate", response_model=CharacterResponse)
async def generate_character_endpoint(
    work_id: str,
    request: CharacterGenerateRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """AI 캐릭터 자동 생성"""
    verify_work_ownership(work_id, current_user.user_id)
    
    try:
        gemini_client = GeminiClient()
        
        # 프롬프트 생성
        personality_text = ", ".join(request.personality_keywords) if request.personality_keywords else "일반적"
        
        prompt = f"""
다음 조건에 맞는 캐릭터 프롬프트를 작성해주세요.

[캐릭터 설명]
{request.description}

[성격 키워드]
{personality_text}

[말투 스타일]
{request.speech_style}

[요구사항]
- 마크다운 형식으로 작성 (## 헤더 사용)
- ## 기본 정보, ## 성격, ## 말투, ## 행동 지침 섹션 포함
- 구체적인 예시 대사 2-3개 포함
- 최대 16,000자 이내

프롬프트만 작성하세요 (설명 없이).
"""
        
        # Gemini API 호출
        generated_prompt = gemini_client.generate_response(prompt)
        
        # 캐릭터 이름 추출 (간단한 추론)
        # 실제로는 더 정교한 파싱 필요
        name = request.description.split()[0] if request.description else "캐릭터"
        
        # 캐릭터 생성
        character_data = CharacterCreate(
            name=name,
            prompt=generated_prompt
        )
        
        character = create_character(work_id, character_data)
        return character
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 캐릭터 생성 실패: {str(e)}"
        )
