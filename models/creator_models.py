"""
창작자 스튜디오 데이터 모델
SYNK 창작자 스튜디오 v1.0
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TargetAudience(str, Enum):
    """타겟 유저"""
    ALL = "all"
    MALE = "male"
    FEMALE = "female"


class Visibility(str, Enum):
    """공개 설정"""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


# ============================================
# 작품 (Work) 모델
# ============================================

class WorkCreate(BaseModel):
    """작품 생성 요청"""
    title: str = Field(..., max_length=50, description="작품 제목")
    description: str = Field(..., max_length=500, description="작품 소개")
    thumbnail_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_items=10, description="태그 (최대 10개)")
    target_audience: TargetAudience = TargetAudience.ALL
    visibility: Visibility = Visibility.PRIVATE
    is_adult: bool = False


class WorkUpdate(BaseModel):
    """작품 수정 요청"""
    title: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    target_audience: Optional[TargetAudience] = None
    visibility: Optional[Visibility] = None
    is_adult: Optional[bool] = None


class WorkResponse(BaseModel):
    """작품 응답"""
    work_id: str
    creator_id: str
    title: str
    description: str
    thumbnail_url: Optional[str]
    tags: List[str]
    target_audience: str
    visibility: str
    is_adult: bool
    view_count: int
    like_count: int
    play_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


# ============================================
# 캐릭터 (Character) 모델
# ============================================

class CharacterCreate(BaseModel):
    """캐릭터 생성 요청"""
    name: str = Field(..., max_length=35, description="캐릭터 이름")
    profile_image_url: Optional[str] = None
    prompt: str = Field(..., max_length=16000, description="캐릭터 프롬프트")


class CharacterUpdate(BaseModel):
    """캐릭터 수정 요청"""
    name: Optional[str] = Field(None, max_length=35)
    profile_image_url: Optional[str] = None
    prompt: Optional[str] = Field(None, max_length=16000)


class CharacterGenerateRequest(BaseModel):
    """AI 캐릭터 생성 요청"""
    description: str = Field(..., max_length=200, description="캐릭터 간단 설명")
    personality_keywords: List[str] = Field(default_factory=list, description="성격 키워드")
    speech_style: str = Field(default="반말", description="말투 스타일")


class CharacterResponse(BaseModel):
    """캐릭터 응답"""
    character_id: str
    work_id: str
    name: str
    profile_image_url: Optional[str]
    prompt: str
    created_at: datetime
    updated_at: datetime


# ============================================
# 이미지 갤러리 (Gallery Image) 모델
# ============================================

class GalleryImageCreate(BaseModel):
    """이미지 생성 요청"""
    character_name: Optional[str] = Field(None, max_length=35, description="캐릭터 이름 (None이면 배경/기타)")
    keyword: str = Field(..., max_length=30, description="키워드 (영문, 숫자, 언더바만)")
    image_url: str = Field(..., description="이미지 URL")
    description: Optional[str] = Field(None, max_length=100, description="설명")


class GalleryImageUpdate(BaseModel):
    """이미지 수정 요청"""
    character_name: Optional[str] = Field(None, max_length=35)
    keyword: Optional[str] = Field(None, max_length=30)
    image_url: Optional[str] = None
    description: Optional[str] = Field(None, max_length=100)


class GalleryImageResponse(BaseModel):
    """이미지 응답"""
    image_id: str
    work_id: str
    character_name: Optional[str]
    keyword: str
    image_url: str
    description: Optional[str]
    usage_code: str
    preview_url: str
    created_at: datetime


# ============================================
# 로어북 (Lorebook) 모델
# ============================================

class LorebookCondition(BaseModel):
    """로어북 활성화 조건"""
    min_intimacy: Optional[float] = None
    min_turns: Optional[int] = None
    required_character: Optional[str] = None


class LorebookEntryCreate(BaseModel):
    """로어북 항목 생성 요청"""
    name: str = Field(..., max_length=80, description="로어 이름")
    keywords: List[str] = Field(..., description="활성화 키워드")
    content: str = Field(..., max_length=4500, description="로어 내용")
    priority: int = Field(default=0, description="우선순위 (낮을수록 높음)")
    conditions: Optional[LorebookCondition] = None


class LorebookEntryUpdate(BaseModel):
    """로어북 항목 수정 요청"""
    name: Optional[str] = Field(None, max_length=80)
    keywords: Optional[List[str]] = None
    content: Optional[str] = Field(None, max_length=4500)
    priority: Optional[int] = None
    conditions: Optional[LorebookCondition] = None


class LorebookEntryResponse(BaseModel):
    """로어북 항목 응답"""
    entry_id: str
    work_id: str
    name: str
    keywords: List[str]
    content: str
    priority: int
    conditions: Optional[dict]
    created_at: datetime
    updated_at: datetime


class LorebookReorderRequest(BaseModel):
    """로어북 순서 변경 요청"""
    entry_ids: List[str] = Field(..., description="항목 ID 순서대로")


# ============================================
# 오프닝 (Opening) 모델
# ============================================

class OpeningCreate(BaseModel):
    """오프닝 생성 요청"""
    title: str = Field(..., max_length=50, description="제목")
    content: str = Field(..., max_length=5500, description="내용")
    is_default: bool = Field(default=False, description="기본 오프닝 여부")
    order_index: int = Field(default=0, description="표시 순서")


class OpeningUpdate(BaseModel):
    """오프닝 수정 요청"""
    title: Optional[str] = Field(None, max_length=50)
    content: Optional[str] = Field(None, max_length=5500)
    is_default: Optional[bool] = None
    order_index: Optional[int] = None


class OpeningResponse(BaseModel):
    """오프닝 응답"""
    opening_id: str
    work_id: str
    title: str
    content: str
    is_default: bool
    order_index: int
    created_at: datetime
    updated_at: datetime
