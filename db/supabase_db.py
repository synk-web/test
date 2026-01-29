"""
Supabase 데이터베이스 연동
SYNK 창작자 스튜디오 - Supabase CRUD 함수
"""
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4
from supabase import Client
from utils.supabase_client import get_supabase_client
from models.creator_models import (
    WorkCreate, WorkUpdate, WorkResponse,
    CharacterCreate, CharacterUpdate, CharacterResponse,
    GalleryImageCreate, GalleryImageUpdate, GalleryImageResponse,
    LorebookEntryCreate, LorebookEntryUpdate, LorebookEntryResponse,
    OpeningCreate, OpeningUpdate, OpeningResponse
)


# ============================================
# 작품 (Works) CRUD
# ============================================

def create_work(creator_id: str, work_data: WorkCreate) -> WorkResponse:
    """작품 생성"""
    supabase = get_supabase_client()
    
    data = {
        "creator_id": creator_id,
        "title": work_data.title,
        "description": work_data.description,
        "thumbnail_url": work_data.thumbnail_url,
        "tags": work_data.tags,
        "target_audience": work_data.target_audience.value,
        "visibility": work_data.visibility.value,
        "is_adult": work_data.is_adult,
    }
    
    result = supabase.table("works").insert(data).execute()
    return WorkResponse(**result.data[0])


def get_work(work_id: str) -> Optional[WorkResponse]:
    """작품 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("works").select("*").eq("work_id", work_id).execute()
    
    if not result.data:
        return None
    
    return WorkResponse(**result.data[0])


def get_works_by_creator(creator_id: str) -> List[WorkResponse]:
    """창작자의 작품 목록 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("works").select("*").eq("creator_id", creator_id).order("created_at", desc=True).execute()
    
    return [WorkResponse(**item) for item in result.data]


def update_work(work_id: str, work_data: WorkUpdate) -> Optional[WorkResponse]:
    """작품 수정"""
    supabase = get_supabase_client()
    
    update_data = work_data.dict(exclude_unset=True)
    if not update_data:
        return get_work(work_id)
    
    # Enum 값 변환
    if "target_audience" in update_data and isinstance(update_data["target_audience"], str):
        update_data["target_audience"] = update_data["target_audience"]
    elif "target_audience" in update_data:
        update_data["target_audience"] = update_data["target_audience"].value
    
    if "visibility" in update_data and isinstance(update_data["visibility"], str):
        update_data["visibility"] = update_data["visibility"]
    elif "visibility" in update_data:
        update_data["visibility"] = update_data["visibility"].value
    
    result = supabase.table("works").update(update_data).eq("work_id", work_id).execute()
    
    if not result.data:
        return None
    
    return WorkResponse(**result.data[0])


def delete_work(work_id: str) -> bool:
    """작품 삭제"""
    supabase = get_supabase_client()
    
    result = supabase.table("works").delete().eq("work_id", work_id).execute()
    
    return len(result.data) > 0


def publish_work(work_id: str) -> Optional[WorkResponse]:
    """작품 발행"""
    supabase = get_supabase_client()
    
    result = supabase.table("works").update({
        "published_at": datetime.now().isoformat(),
        "visibility": "public"
    }).eq("work_id", work_id).execute()
    
    if not result.data:
        return None
    
    return WorkResponse(**result.data[0])


def unpublish_work(work_id: str) -> Optional[WorkResponse]:
    """작품 비공개"""
    supabase = get_supabase_client()
    
    result = supabase.table("works").update({
        "published_at": None,
        "visibility": "private"
    }).eq("work_id", work_id).execute()
    
    if not result.data:
        return None
    
    return WorkResponse(**result.data[0])


# ============================================
# 캐릭터 (Characters) CRUD
# ============================================

def create_character(work_id: str, character_data: CharacterCreate) -> CharacterResponse:
    """캐릭터 생성"""
    supabase = get_supabase_client()
    
    data = {
        "work_id": work_id,
        "name": character_data.name,
        "profile_image_url": character_data.profile_image_url,
        "prompt": character_data.prompt,
    }
    
    result = supabase.table("characters").insert(data).execute()
    return CharacterResponse(**result.data[0])


def get_character(character_id: str) -> Optional[CharacterResponse]:
    """캐릭터 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("characters").select("*").eq("character_id", character_id).execute()
    
    if not result.data:
        return None
    
    return CharacterResponse(**result.data[0])


def get_characters_by_work(work_id: str) -> List[CharacterResponse]:
    """작품의 캐릭터 목록 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("characters").select("*").eq("work_id", work_id).order("created_at").execute()
    
    return [CharacterResponse(**item) for item in result.data]


def update_character(character_id: str, character_data: CharacterUpdate) -> Optional[CharacterResponse]:
    """캐릭터 수정"""
    supabase = get_supabase_client()
    
    update_data = character_data.dict(exclude_unset=True)
    if not update_data:
        return get_character(character_id)
    
    result = supabase.table("characters").update(update_data).eq("character_id", character_id).execute()
    
    if not result.data:
        return None
    
    return CharacterResponse(**result.data[0])


def delete_character(character_id: str) -> bool:
    """캐릭터 삭제"""
    supabase = get_supabase_client()
    
    result = supabase.table("characters").delete().eq("character_id", character_id).execute()
    
    return len(result.data) > 0


# ============================================
# 이미지 갤러리 (Gallery Images) CRUD
# ============================================

def create_gallery_image(work_id: str, image_data: GalleryImageCreate) -> GalleryImageResponse:
    """이미지 생성"""
    supabase = get_supabase_client()
    
    # 사용 코드 생성
    if image_data.character_name:
        usage_code = f"{{{{img::{image_data.character_name}::{image_data.keyword}}}}}"
        preview_url = f"https://synk.app/img/{work_id}/{image_data.character_name}_{image_data.keyword}"
    else:
        usage_code = f"{{{{img::{image_data.keyword}}}}}"
        preview_url = f"https://synk.app/img/{work_id}/{image_data.keyword}"
    
    data = {
        "work_id": work_id,
        "character_name": image_data.character_name,
        "keyword": image_data.keyword,
        "image_url": image_data.image_url,
        "description": image_data.description,
        "usage_code": usage_code,
        "preview_url": preview_url,
    }
    
    result = supabase.table("gallery_images").insert(data).execute()
    return GalleryImageResponse(**result.data[0])


def get_gallery_image(image_id: str) -> Optional[GalleryImageResponse]:
    """이미지 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("gallery_images").select("*").eq("image_id", image_id).execute()
    
    if not result.data:
        return None
    
    return GalleryImageResponse(**result.data[0])


def get_gallery_images_by_work(work_id: str, character_name: Optional[str] = None) -> List[GalleryImageResponse]:
    """작품의 이미지 목록 조회"""
    supabase = get_supabase_client()
    
    query = supabase.table("gallery_images").select("*").eq("work_id", work_id)
    
    if character_name:
        query = query.eq("character_name", character_name)
    
    result = query.order("created_at").execute()
    
    return [GalleryImageResponse(**item) for item in result.data]


def update_gallery_image(image_id: str, image_data: GalleryImageUpdate) -> Optional[GalleryImageResponse]:
    """이미지 수정"""
    supabase = get_supabase_client()
    
    # 기존 이미지 정보 가져오기
    existing = get_gallery_image(image_id)
    if not existing:
        return None
    
    update_data = image_data.dict(exclude_unset=True)
    
    # 키워드나 캐릭터명이 변경되면 usage_code와 preview_url 재생성
    if "keyword" in update_data or "character_name" in update_data:
        char_name = update_data.get("character_name", existing.character_name)
        keyword = update_data.get("keyword", existing.keyword)
        
        if char_name:
            update_data["usage_code"] = f"{{{{img::{char_name}::{keyword}}}}}"
            update_data["preview_url"] = f"https://synk.app/img/{existing.work_id}/{char_name}_{keyword}"
        else:
            update_data["usage_code"] = f"{{{{img::{keyword}}}}}"
            update_data["preview_url"] = f"https://synk.app/img/{existing.work_id}/{keyword}"
    
    if not update_data:
        return existing
    
    result = supabase.table("gallery_images").update(update_data).eq("image_id", image_id).execute()
    
    if not result.data:
        return None
    
    return GalleryImageResponse(**result.data[0])


def delete_gallery_image(image_id: str) -> bool:
    """이미지 삭제"""
    supabase = get_supabase_client()
    
    result = supabase.table("gallery_images").delete().eq("image_id", image_id).execute()
    
    return len(result.data) > 0


# ============================================
# 로어북 (Lorebook) CRUD
# ============================================

def create_lorebook_entry(work_id: str, entry_data: LorebookEntryCreate) -> LorebookEntryResponse:
    """로어북 항목 생성"""
    supabase = get_supabase_client()
    
    data = {
        "work_id": work_id,
        "name": entry_data.name,
        "keywords": entry_data.keywords,
        "content": entry_data.content,
        "priority": entry_data.priority,
        "conditions": entry_data.conditions.dict() if entry_data.conditions else None,
    }
    
    result = supabase.table("lorebook_entries").insert(data).execute()
    return LorebookEntryResponse(**result.data[0])


def get_lorebook_entry(entry_id: str) -> Optional[LorebookEntryResponse]:
    """로어북 항목 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("lorebook_entries").select("*").eq("entry_id", entry_id).execute()
    
    if not result.data:
        return None
    
    return LorebookEntryResponse(**result.data[0])


def get_lorebook_entries_by_work(work_id: str) -> List[LorebookEntryResponse]:
    """작품의 로어북 목록 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("lorebook_entries").select("*").eq("work_id", work_id).order("priority").execute()
    
    return [LorebookEntryResponse(**item) for item in result.data]


def update_lorebook_entry(entry_id: str, entry_data: LorebookEntryUpdate) -> Optional[LorebookEntryResponse]:
    """로어북 항목 수정"""
    supabase = get_supabase_client()
    
    update_data = entry_data.dict(exclude_unset=True)
    
    if "conditions" in update_data and update_data["conditions"]:
        update_data["conditions"] = update_data["conditions"].dict()
    
    if not update_data:
        return get_lorebook_entry(entry_id)
    
    result = supabase.table("lorebook_entries").update(update_data).eq("entry_id", entry_id).execute()
    
    if not result.data:
        return None
    
    return LorebookEntryResponse(**result.data[0])


def delete_lorebook_entry(entry_id: str) -> bool:
    """로어북 항목 삭제"""
    supabase = get_supabase_client()
    
    result = supabase.table("lorebook_entries").delete().eq("entry_id", entry_id).execute()
    
    return len(result.data) > 0


def reorder_lorebook_entries(work_id: str, entry_ids: List[str]) -> bool:
    """로어북 항목 순서 변경"""
    supabase = get_supabase_client()
    
    # 각 항목의 priority 업데이트
    for index, entry_id in enumerate(entry_ids):
        supabase.table("lorebook_entries").update({
            "priority": index
        }).eq("entry_id", entry_id).eq("work_id", work_id).execute()
    
    return True


# ============================================
# 오프닝 (Openings) CRUD
# ============================================

def create_opening(work_id: str, opening_data: OpeningCreate) -> OpeningResponse:
    """오프닝 생성"""
    supabase = get_supabase_client()
    
    # 기본 오프닝이면 기존 기본 오프닝 해제
    if opening_data.is_default:
        supabase.table("openings").update({
            "is_default": False
        }).eq("work_id", work_id).eq("is_default", True).execute()
    
    data = {
        "work_id": work_id,
        "title": opening_data.title,
        "content": opening_data.content,
        "is_default": opening_data.is_default,
        "order_index": opening_data.order_index,
    }
    
    result = supabase.table("openings").insert(data).execute()
    return OpeningResponse(**result.data[0])


def get_opening(opening_id: str) -> Optional[OpeningResponse]:
    """오프닝 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("openings").select("*").eq("opening_id", opening_id).execute()
    
    if not result.data:
        return None
    
    return OpeningResponse(**result.data[0])


def get_openings_by_work(work_id: str) -> List[OpeningResponse]:
    """작품의 오프닝 목록 조회"""
    supabase = get_supabase_client()
    
    result = supabase.table("openings").select("*").eq("work_id", work_id).order("order_index").execute()
    
    return [OpeningResponse(**item) for item in result.data]


def update_opening(opening_id: str, opening_data: OpeningUpdate) -> Optional[OpeningResponse]:
    """오프닝 수정"""
    supabase = get_supabase_client()
    
    # 기본 오프닝으로 설정하면 기존 기본 오프닝 해제
    if opening_data.is_default:
        existing = get_opening(opening_id)
        if existing:
            supabase.table("openings").update({
                "is_default": False
            }).eq("work_id", existing.work_id).eq("is_default", True).neq("opening_id", opening_id).execute()
    
    update_data = opening_data.dict(exclude_unset=True)
    if not update_data:
        return get_opening(opening_id)
    
    result = supabase.table("openings").update(update_data).eq("opening_id", opening_id).execute()
    
    if not result.data:
        return None
    
    return OpeningResponse(**result.data[0])


def delete_opening(opening_id: str) -> bool:
    """오프닝 삭제"""
    supabase = get_supabase_client()
    
    result = supabase.table("openings").delete().eq("opening_id", opening_id).execute()
    
    return len(result.data) > 0


def set_default_opening(work_id: str, opening_id: str) -> Optional[OpeningResponse]:
    """기본 오프닝 설정"""
    supabase = get_supabase_client()
    
    # 기존 기본 오프닝 해제
    supabase.table("openings").update({
        "is_default": False
    }).eq("work_id", work_id).eq("is_default", True).execute()
    
    # 새 기본 오프닝 설정
    result = supabase.table("openings").update({
        "is_default": True
    }).eq("opening_id", opening_id).eq("work_id", work_id).execute()
    
    if not result.data:
        return None
    
    return OpeningResponse(**result.data[0])
