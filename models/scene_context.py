"""
Scene Context 모델
SYNK MVP - 씬 상태 관리 및 맥락 유지
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class CharacterAttention(str, Enum):
    """캐릭터 시선/관심 상태"""
    USER = "user"              # 유저를 보고 있음
    CHARACTER = "character"    # 다른 캐릭터를 보고 있음
    NONE = "none"              # 관심 없음 (졸고 있음 등)
    OBSERVING = "observing"    # 상황 관찰 중


class CharacterState(BaseModel):
    """개별 캐릭터의 현재 상태"""
    
    character_id: str
    character_name: str
    
    # 대화 참여 상태
    recent: bool = False                    # 최근 대화에 참여했는지
    last_spoke_at: Optional[datetime] = None  # 마지막 발화 시간
    turn_count: int = 0                     # 이번 씬에서 발화 횟수
    
    # 시선/관심
    attention: CharacterAttention = CharacterAttention.NONE
    attention_target: Optional[str] = None  # 누구를 보고 있는지 (캐릭터ID 또는 "user")
    
    # 감정/태도
    current_mood: str = "neutral"           # 현재 기분
    mood_intensity: int = 5                 # 기분 강도 (1~10)
    attitude_toward_user: str = "neutral"   # 유저에 대한 태도
    
    # 행동
    last_action: str = ""                   # 마지막 행동
    current_posture: str = ""               # 현재 자세 (서있음, 앉아있음, 기대어있음 등)
    
    # 속마음
    inner_thought: str = ""                 # 현재 속마음
    inner_emotion: str = ""                 # 내면 감정
    
    def to_prompt_context(self) -> str:
        """프롬프트에 주입할 캐릭터 상태"""
        status = "● 최근 대화함" if self.recent else "○ 대화 안함"
        attention_str = {
            CharacterAttention.USER: "유저 주시 중",
            CharacterAttention.CHARACTER: f"{self.attention_target} 주시 중",
            CharacterAttention.NONE: "관심 없음",
            CharacterAttention.OBSERVING: "상황 관찰 중"
        }.get(self.attention, "알 수 없음")
        
        return f"""
[{self.character_name}] {status}
- 시선: {attention_str}
- 기분: {self.current_mood} (강도: {self.mood_intensity}/10)
- 마지막 행동: {self.last_action}
- 속마음: "{self.inner_thought}"
"""


class RecentEvent(BaseModel):
    """최근 대화 이벤트"""
    
    turn_id: str
    speaker_id: str
    speaker_name: str
    target: str                     # "user" 또는 캐릭터 ID
    target_name: str
    action_type: str                # "speak", "react", "interrupt", "observe"
    summary: str                    # "주창윤이 유저에게 시비를 걸음"
    timestamp: datetime = Field(default_factory=datetime.now)


class SceneContext(BaseModel):
    """
    씬 컨텍스트 - 모든 캐릭터가 공유하는 현재 상황
    
    경쟁사(BabeChat) 메모리북 시스템 참고:
    - Story Arc: 전체 스토리 흐름
    - Recent Events: 최근 대화 맥락
    - Character States: 캐릭터별 상태
    """
    
    session_id: str
    location: str
    
    # ═══════════════════════════════════════
    # 1. Story Arc (전체 스토리 흐름)
    # ═══════════════════════════════════════
    story_arc: List[str] = Field(default_factory=list)
    # [
    #   "카카시가 빌런과 배정을 받음",
    #   "베타 동 로비에서 주창윤과 충돌",
    #   "황인하가 끼어들어 주창윤 견제"
    # ]
    
    # ═══════════════════════════════════════
    # 2. Recent Events (최근 대화 맥락) - 가장 중요!
    # ═══════════════════════════════════════
    recent_events: List[RecentEvent] = Field(default_factory=list)
    # 최근 10개 이벤트만 유지
    
    # ═══════════════════════════════════════
    # 3. Character States (캐릭터별 상태)
    # ═══════════════════════════════════════
    character_states: Dict[str, CharacterState] = Field(default_factory=dict)
    
    # ═══════════════════════════════════════
    # 4. Conversation Focus (대화 포커스)
    # ═══════════════════════════════════════
    current_focus: str = ""             # "유저와 황인하의 대화"
    last_speaker_id: Optional[str] = None
    last_speaker_name: Optional[str] = None
    last_target: Optional[str] = None   # "user" 또는 캐릭터 ID
    
    # ═══════════════════════════════════════
    # 5. Scene Atmosphere (분위기)
    # ═══════════════════════════════════════
    tension_level: int = 5              # 긴장도 (1~10)
    atmosphere: str = "neutral"         # "hostile", "friendly", "tense", "calm"
    
    # ═══════════════════════════════════════
    # 메타데이터
    # ═══════════════════════════════════════
    total_turns: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_event(self, event: RecentEvent):
        """이벤트 추가 (최근 10개만 유지)"""
        self.recent_events.append(event)
        if len(self.recent_events) > 10:
            self.recent_events = self.recent_events[-10:]
        
        # 마지막 화자 업데이트
        self.last_speaker_id = event.speaker_id
        self.last_speaker_name = event.speaker_name
        self.last_target = event.target
        
        # 캐릭터 상태 업데이트
        if event.speaker_id in self.character_states:
            state = self.character_states[event.speaker_id]
            state.recent = True
            state.last_spoke_at = event.timestamp
            state.turn_count += 1
            state.last_action = event.summary
        
        self.updated_at = datetime.now()
        self.total_turns += 1
    
    def add_story_point(self, point: str):
        """스토리 포인트 추가 (최근 20개만 유지)"""
        self.story_arc.append(point)
        if len(self.story_arc) > 20:
            self.story_arc = self.story_arc[-20:]
    
    def update_character_state(
        self, 
        character_id: str,
        attention: CharacterAttention = None,
        attention_target: str = None,
        mood: str = None,
        inner_thought: str = None,
        **kwargs
    ):
        """캐릭터 상태 업데이트"""
        if character_id not in self.character_states:
            return
        
        state = self.character_states[character_id]
        if attention:
            state.attention = attention
        if attention_target:
            state.attention_target = attention_target
        if mood:
            state.current_mood = mood
        if inner_thought:
            state.inner_thought = inner_thought
        
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
    
    def get_recent_speakers(self) -> List[str]:
        """최근 대화에 참여한 캐릭터 ID 목록"""
        return [
            char_id for char_id, state in self.character_states.items()
            if state.recent
        ]
    
    def get_characters_watching_user(self) -> List[str]:
        """유저를 주시하고 있는 캐릭터 ID 목록"""
        return [
            char_id for char_id, state in self.character_states.items()
            if state.attention == CharacterAttention.USER
        ]
    
    def reset_recent_flags(self):
        """모든 캐릭터의 recent 플래그 리셋 (새 턴 시작 시)"""
        for state in self.character_states.values():
            state.recent = False
    
    def to_prompt_context(self) -> str:
        """프롬프트에 주입할 전체 씬 컨텍스트"""
        
        # 1. 스토리 요약
        story_summary = "\n".join(f"- {point}" for point in self.story_arc[-5:]) if self.story_arc else "없음"
        
        # 2. 최근 이벤트
        recent_summary = "\n".join(
            f"- {e.speaker_name} → {e.target_name}: {e.summary}"
            for e in self.recent_events[-5:]
        ) if self.recent_events else "없음"
        
        # 3. 캐릭터 상태
        char_status = "\n".join(
            state.to_prompt_context()
            for state in self.character_states.values()
        ) if self.character_states else "없음"
        
        return f"""
═══════════════════════════════════════
[씬 컨텍스트]
═══════════════════════════════════════

📍 장소: {self.location}
🎭 분위기: {self.atmosphere} (긴장도: {self.tension_level}/10)
🎯 현재 대화: {self.current_focus or "없음"}
💬 마지막 화자: {self.last_speaker_name or "없음"}

─────────────────────────────────────
📖 스토리 흐름
─────────────────────────────────────
{story_summary}

─────────────────────────────────────
⏰ 최근 대화
─────────────────────────────────────
{recent_summary}

─────────────────────────────────────
👥 캐릭터 상태
─────────────────────────────────────
{char_status}

═══════════════════════════════════════
"""


# ═══════════════════════════════════════════════════════════════
# 씬 컨텍스트 생성 헬퍼
# ═══════════════════════════════════════════════════════════════

def create_scene_context(
    session_id: str,
    location: str,
    characters: List[dict]
) -> SceneContext:
    """
    새 씬 컨텍스트 생성
    
    Args:
        session_id: 세션 ID
        location: 장소 이름
        characters: 해당 장소의 캐릭터 목록
    """
    context = SceneContext(
        session_id=session_id,
        location=location
    )
    
    # 캐릭터 상태 초기화
    for char in characters:
        context.character_states[char["id"]] = CharacterState(
            character_id=char["id"],
            character_name=char["name"],
            current_mood=char.get("default_emotion", "neutral"),
            current_posture=char.get("default_posture", "서있음"),
            attention=CharacterAttention.OBSERVING,
            inner_thought=f"새로운 사람이 왔군..."
        )
    
    return context
