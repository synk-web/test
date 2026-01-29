"""
관계 데이터 모델
SYNK MVP - 유저와 캐릭터 간의 관계 데이터
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EmotionalStats(BaseModel):
    """감정 통계"""
    joy_peaks: int = 0          # 기쁨 피크 횟수
    anger_peaks: int = 0        # 화남 피크 횟수
    excitement_peaks: int = 0   # 열광 피크 횟수
    sadness_peaks: int = 0      # 슬픔 피크 횟수
    fear_peaks: int = 0         # 두려움 피크 횟수


class Dominance(BaseModel):
    """권력 구조 (Dominance)"""
    score: float = 0.0          # -1.0 ~ 1.0
    history: List[float] = Field(default_factory=list)  # 히스토리


class CoreMemory(BaseModel):
    """핵심 기억"""
    summary: str                # 기억 요약
    memorable_quote: Optional[str] = None  # 기억에 남는 대사
    timestamp: datetime = Field(default_factory=datetime.now)
    trigger_keywords: List[str] = Field(default_factory=list)  # 트리거 키워드
    emotion: Optional[str] = None  # 감정


class TriggerKeyword(BaseModel):
    """트리거 키워드"""
    keyword: str                # 키워드
    emotion: str                # 감정 (anger, joy, etc.)
    occurrence_count: int = 1   # 발생 횟수
    confidence: float = 0.5     # 신뢰도 (0.0 ~ 1.0)
    first_occurrence: datetime = Field(default_factory=datetime.now)


class RelationshipData(BaseModel):
    """관계 데이터"""
    user_id: str
    character_id: str
    
    # 친밀도
    intimacy: float = 0.0       # 0.0 ~ 10.0
    
    # 권력 구조
    dominance: Dominance = Field(default_factory=Dominance)
    
    # 감정 통계
    emotional_stats: EmotionalStats = Field(default_factory=EmotionalStats)
    
    # 핵심 기억
    core_memories: List[CoreMemory] = Field(default_factory=list)
    
    # 트리거 키워드
    trigger_keywords: List[TriggerKeyword] = Field(default_factory=list)
    
    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_turns: int = 0        # 총 대화 턴 수
