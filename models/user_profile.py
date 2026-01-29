"""
유저 프로필 모델
SYNK MVP - 주인공(유저) 정보 저장
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CharacterImpression(BaseModel):
    """캐릭터가 유저에 대해 가진 인상"""
    status: str = "neutral"              # "적대적", "우호적", "경계", "무관심"
    impression: str = ""                 # "만만해 보이는 놈"
    key_events: List[str] = Field(default_factory=list)  # ["상의를 찢음", "싸움을 걸음"]
    last_updated: datetime = Field(default_factory=datetime.now)


class UserAction(BaseModel):
    """유저의 주요 행동 기록"""
    action: str                          # "주창윤의 상의를 찢음"
    location: str                        # "베타_동_로비"
    involved_characters: List[str] = []  # ["npc_joo_changyun"]
    timestamp: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """
    유저 프로필 (주인공 정보)
    
    대화를 통해 자동으로 업데이트되며,
    캐릭터들이 유저를 기억하고 개인화된 반응을 하는 데 사용됩니다.
    """
    
    user_id: str
    
    # ═══════════════════════════════════════
    # 기본 정보 (유저 직접 입력 또는 대화에서 추출)
    # ═══════════════════════════════════════
    nickname: Optional[str] = None       # "카카시"
    gender: Optional[str] = None         # "male" / "female" / "other"
    
    # ═══════════════════════════════════════
    # 능력 정보 (대화에서 자동 추출)
    # ═══════════════════════════════════════
    ability_name: Optional[str] = None           # "뇌절"
    ability_description: Optional[str] = None    # "손끝에 전기를 모아 적의 심장을 관통"
    ability_rank: Optional[str] = None           # 추정 등급 (S/A/B/C/D)
    ability_type: Optional[str] = None           # "전기", "물리", "정신" 등
    
    # ═══════════════════════════════════════
    # 성격/특성 (대화 패턴에서 자동 분석)
    # ═══════════════════════════════════════
    personality_traits: List[str] = Field(default_factory=list)
    # 예: ["도발적", "자신감", "충동적", "유머러스"]
    
    speech_style: Optional[str] = None   # "반말, 도발적, 유머 섞음"
    
    # ═══════════════════════════════════════
    # 캐릭터별 관계 (캐릭터가 유저를 어떻게 보는지)
    # ═══════════════════════════════════════
    character_impressions: Dict[str, CharacterImpression] = Field(default_factory=dict)
    # {
    #   "npc_joo_changyun": CharacterImpression(
    #     status="적대적",
    #     impression="만만해 보이는 놈",
    #     key_events=["상의를 찢음"]
    #   )
    # }
    
    # ═══════════════════════════════════════
    # 행동 히스토리
    # ═══════════════════════════════════════
    key_actions: List[UserAction] = Field(default_factory=list)
    # 주요 행동만 기록 (일반 대화는 제외)
    
    mentioned_facts: List[str] = Field(default_factory=list)
    # 유저가 언급한 사실들: ["뇌절 능력 보유", "전투를 즐김"]
    
    # ═══════════════════════════════════════
    # 선호도 (자동 분석)
    # ═══════════════════════════════════════
    likes: List[str] = Field(default_factory=list)      # 좋아하는 것
    dislikes: List[str] = Field(default_factory=list)   # 싫어하는 것
    
    # ═══════════════════════════════════════
    # 통계
    # ═══════════════════════════════════════
    total_turns: int = 0                 # 총 대화 턴 수
    favorite_character: Optional[str] = None  # 가장 많이 대화한 캐릭터
    
    # ═══════════════════════════════════════
    # 메타데이터
    # ═══════════════════════════════════════
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_action(self, action: str, location: str, characters: List[str] = None):
        """주요 행동 추가"""
        self.key_actions.append(UserAction(
            action=action,
            location=location,
            involved_characters=characters or [],
            timestamp=datetime.now()
        ))
        # 최근 50개만 유지
        if len(self.key_actions) > 50:
            self.key_actions = self.key_actions[-50:]
        self.updated_at = datetime.now()
    
    def update_character_impression(
        self, 
        character_id: str, 
        status: str = None,
        impression: str = None,
        event: str = None
    ):
        """캐릭터의 유저에 대한 인상 업데이트"""
        if character_id not in self.character_impressions:
            self.character_impressions[character_id] = CharacterImpression()
        
        imp = self.character_impressions[character_id]
        
        if status:
            imp.status = status
        if impression:
            imp.impression = impression
        if event:
            imp.key_events.append(event)
            # 최근 10개만 유지
            if len(imp.key_events) > 10:
                imp.key_events = imp.key_events[-10:]
        
        imp.last_updated = datetime.now()
        self.updated_at = datetime.now()
    
    def add_trait(self, trait: str):
        """성격 특성 추가"""
        if trait not in self.personality_traits:
            self.personality_traits.append(trait)
            # 최대 10개
            if len(self.personality_traits) > 10:
                self.personality_traits = self.personality_traits[-10:]
        self.updated_at = datetime.now()
    
    def add_fact(self, fact: str):
        """새로운 사실 추가"""
        if fact not in self.mentioned_facts:
            self.mentioned_facts.append(fact)
            # 최대 30개
            if len(self.mentioned_facts) > 30:
                self.mentioned_facts = self.mentioned_facts[-30:]
        self.updated_at = datetime.now()
    
    def to_prompt_context(self) -> str:
        """프롬프트에 주입할 유저 정보"""
        
        context = f"""
[유저(주인공) 정보]
- 이름: {self.nickname or "알 수 없음"}
- 능력: {self.ability_name or "알 수 없음"}
"""
        if self.ability_description:
            context += f"  └ {self.ability_description}\n"
        
        if self.personality_traits:
            context += f"- 성격: {', '.join(self.personality_traits)}\n"
        
        if self.key_actions:
            recent_actions = [a.action for a in self.key_actions[-3:]]
            context += f"- 최근 행동: {', '.join(recent_actions)}\n"
        
        return context
