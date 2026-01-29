"""
캐릭터 모델
SYNK MVP - DB 기반 캐릭터 시스템
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CharacterPersona(BaseModel):
    """캐릭터 페르소나 모델"""
    
    # ═══════════════════════════════════════
    # 기본 정보
    # ═══════════════════════════════════════
    id: str                          # "npc_lee_gaeun"
    name: str                        # "이가은"
    location: str                    # "아카데미_정문"
    
    # ═══════════════════════════════════════
    # 성격 및 말투
    # ═══════════════════════════════════════
    personality: str                 # 성격 설명
    speech_style: str = ""           # 말투 패턴
    speech_examples: List[str] = Field(default_factory=list)  # 말투 예시
    
    # ═══════════════════════════════════════
    # 배경 스토리
    # ═══════════════════════════════════════
    background: str = ""             # 배경 스토리
    secrets: List[str] = Field(default_factory=list)  # 비밀 (친밀도 높으면 공개)
    
    # ═══════════════════════════════════════
    # 유저와의 관계 기본값
    # ═══════════════════════════════════════
    user_relationship: str = "stranger"  # 유저와의 기본 관계
    dominance_default: float = 0.0       # 초기 권력 구조 (-1.0 ~ 1.0)
    
    # ═══════════════════════════════════════
    # 감정 트리거 (핵심 데이터 연동용)
    # ═══════════════════════════════════════
    emotion_triggers: Dict[str, str] = Field(default_factory=dict)  # {"오이": "anger"}
    sensitive_topics: List[str] = Field(default_factory=list)       # 민감한 주제
    
    # ═══════════════════════════════════════
    # 능력 및 태그
    # ═══════════════════════════════════════
    tags: List[str] = Field(default_factory=list)
    ability: Optional[str] = None        # 능력
    ability_rank: Optional[str] = None   # 등급 (S/A/B/C/D)
    
    # ═══════════════════════════════════════
    # XR 전환용 데이터
    # ═══════════════════════════════════════
    default_emotion: str = "neutral"     # 기본 표정
    default_posture: str = "standing"    # 기본 자세
    voice_tone: str = "normal"           # 목소리 톤
    
    # ═══════════════════════════════════════
    # 메타데이터
    # ═══════════════════════════════════════
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def to_prompt(self, include_secrets: bool = False) -> str:
        """캐릭터 프롬프트 생성"""
        prompt = f"""
[캐릭터 정보]
이름: {self.name}
성격: {self.personality}
말투: {self.speech_style}
배경: {self.background}
"""
        if self.speech_examples:
            prompt += f"말투 예시: {', '.join(self.speech_examples[:3])}\n"
        
        if include_secrets and self.secrets:
            prompt += f"비밀: {', '.join(self.secrets)}\n"
        
        if self.emotion_triggers:
            triggers = [f"'{k}' 언급 시 {v}" for k, v in self.emotion_triggers.items()]
            prompt += f"감정 트리거: {', '.join(triggers)}\n"
        
        return prompt


class Location(BaseModel):
    """장소 모델"""
    id: str                          # "베타_동_로비"
    name: str                        # "베타 동 로비"
    description: str = ""            # 장소 설명
    atmosphere: str = ""             # 분위기
    tags: List[str] = Field(default_factory=list)
