"""
캐릭터 API
SYNK MVP - 캐릭터 CRUD 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.character import CharacterPersona, Location
from db.character_db import (
    get_db,
    create_character,
    get_character,
    get_characters_by_location,
    get_all_characters,
    update_character,
    delete_character,
    create_location,
    get_location,
    get_all_locations,
)

router = APIRouter(prefix="/api/character", tags=["character"])


# ═══════════════════════════════════════════════════════════
# 요청/응답 모델
# ═══════════════════════════════════════════════════════════

class CharacterCreateRequest(BaseModel):
    """캐릭터 생성 요청"""
    id: str
    name: str
    location: str
    personality: str
    speech_style: str = ""
    speech_examples: List[str] = []
    background: str = ""
    secrets: List[str] = []
    user_relationship: str = "stranger"
    dominance_default: float = 0.0
    emotion_triggers: dict = {}
    sensitive_topics: List[str] = []
    tags: List[str] = []
    ability: Optional[str] = None
    ability_rank: Optional[str] = None
    default_emotion: str = "neutral"
    default_posture: str = "standing"
    voice_tone: str = "normal"


class CharacterUpdateRequest(BaseModel):
    """캐릭터 수정 요청"""
    name: Optional[str] = None
    location: Optional[str] = None
    personality: Optional[str] = None
    speech_style: Optional[str] = None
    speech_examples: Optional[List[str]] = None
    background: Optional[str] = None
    secrets: Optional[List[str]] = None
    user_relationship: Optional[str] = None
    dominance_default: Optional[float] = None
    emotion_triggers: Optional[dict] = None
    sensitive_topics: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    ability: Optional[str] = None
    ability_rank: Optional[str] = None
    default_emotion: Optional[str] = None
    default_posture: Optional[str] = None
    voice_tone: Optional[str] = None


class LocationCreateRequest(BaseModel):
    """장소 생성 요청"""
    id: str
    name: str
    description: str = ""
    atmosphere: str = ""
    tags: List[str] = []


# ═══════════════════════════════════════════════════════════
# 캐릭터 API
# ═══════════════════════════════════════════════════════════

@router.post("/", response_model=dict)
async def api_create_character(
    request: CharacterCreateRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 생성"""
    # 중복 확인
    existing = get_character(request.id, db)
    if existing:
        raise HTTPException(status_code=400, detail=f"캐릭터 ID '{request.id}'가 이미 존재합니다.")
    
    char = CharacterPersona(**request.dict())
    created = create_character(char, db)
    
    return {
        "success": True,
        "message": f"캐릭터 '{created.name}' 생성 완료",
        "character": created.dict()
    }


@router.get("/{character_id}", response_model=dict)
async def api_get_character(
    character_id: str,
    db: Session = Depends(get_db)
):
    """캐릭터 조회"""
    char = get_character(character_id, db)
    if not char:
        raise HTTPException(status_code=404, detail=f"캐릭터 '{character_id}'를 찾을 수 없습니다.")
    
    return {
        "success": True,
        "character": char.dict()
    }


@router.get("/", response_model=dict)
async def api_get_all_characters(
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """모든 캐릭터 조회 (장소 필터 가능)"""
    if location:
        characters = get_characters_by_location(location, db)
    else:
        characters = get_all_characters(db)
    
    return {
        "success": True,
        "count": len(characters),
        "characters": [c.dict() for c in characters]
    }


@router.put("/{character_id}", response_model=dict)
async def api_update_character(
    character_id: str,
    request: CharacterUpdateRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 수정"""
    # None이 아닌 필드만 추출
    updates = {k: v for k, v in request.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다.")
    
    updated = update_character(character_id, updates, db)
    if not updated:
        raise HTTPException(status_code=404, detail=f"캐릭터 '{character_id}'를 찾을 수 없습니다.")
    
    return {
        "success": True,
        "message": f"캐릭터 '{updated.name}' 수정 완료",
        "character": updated.dict()
    }


@router.delete("/{character_id}", response_model=dict)
async def api_delete_character(
    character_id: str,
    db: Session = Depends(get_db)
):
    """캐릭터 삭제"""
    deleted = delete_character(character_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"캐릭터 '{character_id}'를 찾을 수 없습니다.")
    
    return {
        "success": True,
        "message": f"캐릭터 '{character_id}' 삭제 완료"
    }


# ═══════════════════════════════════════════════════════════
# 장소 API
# ═══════════════════════════════════════════════════════════

@router.post("/location/", response_model=dict)
async def api_create_location(
    request: LocationCreateRequest,
    db: Session = Depends(get_db)
):
    """장소 생성"""
    existing = get_location(request.id, db)
    if existing:
        raise HTTPException(status_code=400, detail=f"장소 ID '{request.id}'가 이미 존재합니다.")
    
    loc = Location(**request.dict())
    created = create_location(loc, db)
    
    return {
        "success": True,
        "message": f"장소 '{created.name}' 생성 완료",
        "location": created.dict()
    }


@router.get("/location/", response_model=dict)
async def api_get_all_locations(
    db: Session = Depends(get_db)
):
    """모든 장소 조회"""
    locations = get_all_locations(db)
    
    return {
        "success": True,
        "count": len(locations),
        "locations": [l.dict() for l in locations]
    }


@router.get("/location/{location_id}", response_model=dict)
async def api_get_location(
    location_id: str,
    db: Session = Depends(get_db)
):
    """장소 조회 (해당 장소의 캐릭터들 포함)"""
    loc = get_location(location_id, db)
    if not loc:
        raise HTTPException(status_code=404, detail=f"장소 '{location_id}'를 찾을 수 없습니다.")
    
    characters = get_characters_by_location(location_id, db)
    
    return {
        "success": True,
        "location": loc.dict(),
        "characters": [c.dict() for c in characters]
    }
