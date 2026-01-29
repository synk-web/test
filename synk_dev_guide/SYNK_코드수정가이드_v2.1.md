# SYNK MVP 코드 수정 가이드 v2.1

> **목적**: 기존 코드에 맥락 유지 시스템 추가
> **핵심 문제**: 대화 맥락 파괴, 캐릭터 간 케미 부재
> **해결책**: Scene Context 시스템 도입

---

## 📋 목차

1. [문제 분석](#1-문제-분석)
2. [Scene Context 시스템](#2-scene-context-시스템)
3. [Speaker Selector 개선](#3-speaker-selector-개선)
4. [이모지 리액션 시스템](#4-이모지-리액션-시스템)
5. [유저 프로필 시스템](#5-유저-프로필-시스템)
6. [캐릭터 속마음 시스템](#6-캐릭터-속마음-시스템)
7. [Scene Dashboard UI](#7-scene-dashboard-ui)
8. [API 수정 사항](#8-api-수정-사항)
9. [개발 우선순위](#9-개발-우선순위)

---

# 1. 문제 분석

## 1.1 현재 발생하는 문제

### 문제 1: 맥락 파괴

```
[실제 대화 로그]

황인하: "후후... 굳이 대답해야 하나? 뭐, 좋아..."

유저: "넌뭔데 누군데"  ← 황인하에게 질문

민아름: "후아... 누구냐니... 내가 알 바... 아니잖아..."  ← ❌ 엉뚱한 캐릭터 응답!
```

**원인**: 
- "넌", "너" 같은 대명사를 처리하지 못함
- 직전 대화 상대를 추적하지 않음
- 랜덤으로 화자 선택됨

### 문제 2: 캐릭터 간 케미 없음

```
현재 구조:
┌─────────┐     ┌─────────┐     ┌─────────┐
│ 주창윤   │     │ 황인하   │     │ 민아름   │
│         │     │         │     │         │
│ (유저만  │     │ (유저만  │     │ (유저만  │
│  인식)   │     │  인식)   │     │  인식)   │
└─────────┘     └─────────┘     └─────────┘

필요한 구조:
┌─────────────────────────────────────────┐
│           Scene Context (공유)           │
│                                         │
│  • 현재 상황: 주창윤과 유저가 싸우는 중    │
│  • 황인하가 끼어들어 견제함               │
│  • 민아름은 구석에서 졸고 있음            │
│                                         │
└─────────────────────────────────────────┘
         ▲           ▲           ▲
         │           │           │
    ┌────┴───┐  ┌────┴───┐  ┌────┴───┐
    │ 주창윤  │  │ 황인하  │  │ 민아름  │
    └────────┘  └────────┘  └────────┘
```

---

# 2. Scene Context 시스템

## 2.1 개요

경쟁사(BabeChat)의 "메모리북" 시스템을 참고한 **씬 컨텍스트 시스템**입니다.
모든 캐릭터가 현재 상황을 공유하여 맥락을 유지합니다.

## 2.2 새 파일 생성: `models/scene_context.py`

```python
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
        story_summary = "\n".join(f"- {point}" for point in self.story_arc[-5:])
        
        # 2. 최근 이벤트
        recent_summary = "\n".join(
            f"- {e.speaker_name} → {e.target_name}: {e.summary}"
            for e in self.recent_events[-5:]
        )
        
        # 3. 캐릭터 상태
        char_status = "\n".join(
            state.to_prompt_context()
            for state in self.character_states.values()
        )
        
        return f"""
═══════════════════════════════════════
[씬 컨텍스트]
═══════════════════════════════════════

📍 장소: {self.location}
🎭 분위기: {self.atmosphere} (긴장도: {self.tension_level}/10)
🎯 현재 대화: {self.current_focus}
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
            current_mood=char.get("default_mood", "neutral"),
            current_posture=char.get("default_posture", "서있음"),
            attention=CharacterAttention.OBSERVING,
            inner_thought=f"새로운 사람이 왔군..."
        )
    
    return context
```

## 2.3 새 파일 생성: `core/scene_manager.py`

```python
"""
Scene Manager
SYNK MVP - 씬 상태 관리 및 업데이트
"""
from typing import Optional, List, Dict
from datetime import datetime
import re

from models.scene_context import (
    SceneContext, 
    CharacterState, 
    RecentEvent,
    CharacterAttention,
    create_scene_context
)


class SceneManager:
    """씬 상태 관리자"""
    
    def __init__(self):
        # 세션별 씬 컨텍스트 저장
        self._contexts: Dict[str, SceneContext] = {}
    
    def get_or_create_context(
        self, 
        session_id: str, 
        location: str,
        characters: List[dict]
    ) -> SceneContext:
        """씬 컨텍스트 조회 또는 생성"""
        if session_id not in self._contexts:
            self._contexts[session_id] = create_scene_context(
                session_id, location, characters
            )
        return self._contexts[session_id]
    
    def get_context(self, session_id: str) -> Optional[SceneContext]:
        """씬 컨텍스트 조회"""
        return self._contexts.get(session_id)
    
    def process_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str = "user"
    ) -> dict:
        """
        유저 메시지 처리 및 대화 대상 분석
        
        Returns:
            {
                "target_type": "direct" | "pronoun" | "recent" | "random",
                "target_id": 캐릭터 ID 또는 None,
                "target_name": 캐릭터 이름 또는 None,
                "analysis": 분석 결과 설명
            }
        """
        context = self.get_context(session_id)
        if not context:
            return {"target_type": "random", "target_id": None, "analysis": "컨텍스트 없음"}
        
        result = {
            "target_type": "random",
            "target_id": None,
            "target_name": None,
            "analysis": ""
        }
        
        # 1. 직접 이름 멘션 체크
        for char_id, state in context.character_states.items():
            if state.character_name in user_message:
                result["target_type"] = "direct"
                result["target_id"] = char_id
                result["target_name"] = state.character_name
                result["analysis"] = f"'{state.character_name}' 직접 호출"
                return result
        
        # 2. 대명사 체크 → 직전 화자에게 응답
        pronouns = ["넌", "너", "니가", "네가", "당신", "니", "네"]
        if any(p in user_message for p in pronouns):
            if context.last_speaker_id:
                result["target_type"] = "pronoun"
                result["target_id"] = context.last_speaker_id
                result["target_name"] = context.last_speaker_name
                result["analysis"] = f"대명사 사용 → 직전 화자 '{context.last_speaker_name}'"
                return result
        
        # 3. 최근 대화 참여자 우선
        recent_speakers = context.get_recent_speakers()
        if recent_speakers:
            # 가장 최근에 말한 캐릭터
            last_id = context.last_speaker_id
            if last_id and last_id in recent_speakers:
                state = context.character_states[last_id]
                result["target_type"] = "recent"
                result["target_id"] = last_id
                result["target_name"] = state.character_name
                result["analysis"] = f"최근 화자 '{state.character_name}' 선택"
                return result
        
        # 4. 유저를 주시하는 캐릭터 우선
        watching_user = context.get_characters_watching_user()
        if watching_user:
            char_id = watching_user[0]
            state = context.character_states[char_id]
            result["target_type"] = "attention"
            result["target_id"] = char_id
            result["target_name"] = state.character_name
            result["analysis"] = f"유저 주시 중인 '{state.character_name}' 선택"
            return result
        
        # 5. 활성 캐릭터 중 랜덤 (졸고 있는 캐릭터 제외)
        active_chars = [
            (char_id, state) 
            for char_id, state in context.character_states.items()
            if state.attention != CharacterAttention.NONE
        ]
        if active_chars:
            import random
            char_id, state = random.choice(active_chars)
            result["target_type"] = "random_active"
            result["target_id"] = char_id
            result["target_name"] = state.character_name
            result["analysis"] = f"활성 캐릭터 중 '{state.character_name}' 랜덤 선택"
            return result
        
        result["analysis"] = "적절한 대상 없음"
        return result
    
    def process_character_response(
        self,
        session_id: str,
        character_id: str,
        character_name: str,
        response: str,
        target: str = "user",
        target_name: str = "유저",
        inner_thought: str = None,
        mood: str = None
    ):
        """
        캐릭터 응답 처리 및 씬 컨텍스트 업데이트
        """
        context = self.get_context(session_id)
        if not context:
            return
        
        # 이벤트 추가
        event = RecentEvent(
            turn_id=f"turn_{context.total_turns + 1}",
            speaker_id=character_id,
            speaker_name=character_name,
            target=target,
            target_name=target_name,
            action_type="speak",
            summary=self._summarize_response(response)
        )
        context.add_event(event)
        
        # 캐릭터 상태 업데이트
        context.update_character_state(
            character_id,
            attention=CharacterAttention.USER if target == "user" else CharacterAttention.CHARACTER,
            attention_target=target,
            mood=mood,
            inner_thought=inner_thought
        )
        
        # 현재 포커스 업데이트
        context.current_focus = f"{character_name}와 {target_name}의 대화"
        
        # 다른 캐릭터들의 시선 업데이트 (대화 참여자를 주시)
        for char_id, state in context.character_states.items():
            if char_id != character_id:
                if state.attention != CharacterAttention.NONE:
                    state.attention = CharacterAttention.OBSERVING
    
    def add_story_point(self, session_id: str, point: str):
        """스토리 포인트 추가"""
        context = self.get_context(session_id)
        if context:
            context.add_story_point(point)
    
    def update_tension(self, session_id: str, delta: int):
        """긴장도 조절"""
        context = self.get_context(session_id)
        if context:
            context.tension_level = max(1, min(10, context.tension_level + delta))
    
    def _summarize_response(self, response: str, max_length: int = 50) -> str:
        """응답 요약"""
        # 간단한 요약 (첫 문장 또는 일부)
        first_sentence = response.split('.')[0].split('!')[0].split('?')[0]
        if len(first_sentence) > max_length:
            return first_sentence[:max_length] + "..."
        return first_sentence


# 전역 인스턴스
scene_manager = SceneManager()
```

---

# 3. Speaker Selector 개선

## 3.1 파일 수정: `core/speaker_selector.py`

**기존 코드 위치 확인 후 아래 로직으로 교체/보완**

```python
"""
Speaker Selector 개선
SYNK MVP - 대명사 처리 및 맥락 기반 화자 선택
"""
from typing import List, Dict, Optional, Tuple
from models.scene_context import SceneContext, CharacterAttention


# ═══════════════════════════════════════════════════════════════
# 대명사 목록
# ═══════════════════════════════════════════════════════════════

PRONOUNS_TO_LAST_SPEAKER = [
    # 2인칭 대명사 (직전 화자 지칭)
    "넌", "너", "니가", "네가", "당신", "니", "네",
    "너는", "네가", "니가", "당신은", "당신이"
]

PRONOUNS_TO_SELF = [
    # 1인칭 대명사 (유저 자신)
    "나", "난", "내가", "저", "제가"
]


# ═══════════════════════════════════════════════════════════════
# 메인 함수: 화자 선택
# ═══════════════════════════════════════════════════════════════

def select_speaker_v2(
    user_message: str,
    location_characters: List[Dict],
    scene_context: Optional[SceneContext] = None,
    conversation_history: List[Dict] = None
) -> Tuple[str, str, str]:
    """
    개선된 화자 선택 로직
    
    Args:
        user_message: 유저 메시지
        location_characters: 해당 장소의 캐릭터 목록
        scene_context: 씬 컨텍스트 (있으면 사용)
        conversation_history: 대화 히스토리 (scene_context 없을 때 폴백)
    
    Returns:
        (character_id, character_name, selection_reason)
    
    선택 우선순위:
    1. 직접 이름 멘션
    2. @ 멘션
    3. 대명사 → 직전 화자
    4. 최근 대화 참여자 (recent 태그)
    5. 유저 주시 중인 캐릭터
    6. 활성 캐릭터 중 랜덤
    """
    
    # 캐릭터 이름 → ID 매핑
    name_to_char = {char["name"]: char for char in location_characters}
    id_to_char = {char["id"]: char for char in location_characters}
    
    # ─────────────────────────────────────
    # 1. 직접 이름 멘션 체크
    # ─────────────────────────────────────
    for char in location_characters:
        if char["name"] in user_message:
            return char["id"], char["name"], f"direct_mention:{char['name']}"
    
    # ─────────────────────────────────────
    # 2. @ 멘션 체크
    # ─────────────────────────────────────
    for char in location_characters:
        if f"@{char['name']}" in user_message:
            return char["id"], char["name"], f"at_mention:@{char['name']}"
    
    # Scene Context가 있는 경우
    if scene_context:
        return _select_with_context(user_message, location_characters, scene_context)
    
    # Scene Context가 없는 경우 (폴백)
    return _select_without_context(user_message, location_characters, conversation_history)


def _select_with_context(
    user_message: str,
    location_characters: List[Dict],
    context: SceneContext
) -> Tuple[str, str, str]:
    """Scene Context를 사용한 화자 선택"""
    
    # ─────────────────────────────────────
    # 3. 대명사 체크 → 직전 화자
    # ─────────────────────────────────────
    for pronoun in PRONOUNS_TO_LAST_SPEAKER:
        if pronoun in user_message:
            if context.last_speaker_id:
                char = next(
                    (c for c in location_characters if c["id"] == context.last_speaker_id),
                    None
                )
                if char:
                    return char["id"], char["name"], f"pronoun:{pronoun}→{char['name']}"
    
    # ─────────────────────────────────────
    # 4. 최근 대화 참여자 (recent 태그)
    # ─────────────────────────────────────
    recent_speakers = context.get_recent_speakers()
    if recent_speakers and context.last_speaker_id in recent_speakers:
        char = next(
            (c for c in location_characters if c["id"] == context.last_speaker_id),
            None
        )
        if char:
            return char["id"], char["name"], f"recent_speaker:{char['name']}"
    
    # ─────────────────────────────────────
    # 5. 유저 주시 중인 캐릭터
    # ─────────────────────────────────────
    watching_user = context.get_characters_watching_user()
    if watching_user:
        char_id = watching_user[0]
        char = next(
            (c for c in location_characters if c["id"] == char_id),
            None
        )
        if char:
            return char["id"], char["name"], f"attention_user:{char['name']}"
    
    # ─────────────────────────────────────
    # 6. 활성 캐릭터 중 랜덤 (졸고 있는 캐릭터 제외)
    # ─────────────────────────────────────
    active_chars = []
    for char in location_characters:
        state = context.character_states.get(char["id"])
        if state and state.attention != CharacterAttention.NONE:
            active_chars.append(char)
    
    if active_chars:
        import random
        char = random.choice(active_chars)
        return char["id"], char["name"], f"random_active:{char['name']}"
    
    # 최후의 수단: 전체 랜덤
    import random
    char = random.choice(location_characters)
    return char["id"], char["name"], f"random_fallback:{char['name']}"


def _select_without_context(
    user_message: str,
    location_characters: List[Dict],
    conversation_history: List[Dict] = None
) -> Tuple[str, str, str]:
    """Scene Context 없이 화자 선택 (폴백)"""
    
    # 대명사 체크 + 히스토리에서 마지막 화자 찾기
    if conversation_history:
        for pronoun in PRONOUNS_TO_LAST_SPEAKER:
            if pronoun in user_message:
                # 히스토리에서 마지막 NPC 화자 찾기
                for msg in reversed(conversation_history):
                    if msg.get("role") == "assistant" and msg.get("character_id"):
                        char = next(
                            (c for c in location_characters if c["id"] == msg["character_id"]),
                            None
                        )
                        if char:
                            return char["id"], char["name"], f"pronoun_history:{pronoun}→{char['name']}"
    
    # 마지막 대화 상대 유지
    if conversation_history:
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant" and msg.get("character_id"):
                char = next(
                    (c for c in location_characters if c["id"] == msg["character_id"]),
                    None
                )
                if char:
                    return char["id"], char["name"], f"last_speaker:{char['name']}"
    
    # 랜덤
    import random
    char = random.choice(location_characters)
    return char["id"], char["name"], f"random:{char['name']}"


# ═══════════════════════════════════════════════════════════════
# 유틸리티 함수
# ═══════════════════════════════════════════════════════════════

def detect_mentioned_characters(
    text: str,
    characters: List[Dict]
) -> List[Dict]:
    """텍스트에서 언급된 캐릭터 감지"""
    mentioned = []
    for char in characters:
        if char["name"] in text:
            mentioned.append(char)
    return mentioned


def should_character_intervene(
    character: Dict,
    scene_context: SceneContext,
    trigger_keywords: List[str] = None
) -> Tuple[bool, str]:
    """
    캐릭터가 대화에 끼어들어야 하는지 판단
    
    Returns:
        (should_intervene, reason)
    """
    char_id = character["id"]
    state = scene_context.character_states.get(char_id)
    
    if not state:
        return False, ""
    
    # 1. 이미 최근 대화에 참여 중이면 패스
    if state.recent:
        return False, ""
    
    # 2. 관심 없는 상태면 패스
    if state.attention == CharacterAttention.NONE:
        return False, ""
    
    # 3. 트리거 키워드 체크
    if trigger_keywords:
        for event in scene_context.recent_events[-3:]:
            for keyword in trigger_keywords:
                if keyword in event.summary:
                    return True, f"trigger_keyword:{keyword}"
    
    # 4. 긴장도가 높고 3턴 이상 대화 시 20% 확률로 난입
    if scene_context.tension_level >= 7 and scene_context.total_turns >= 3:
        import random
        if random.random() < 0.2:
            return True, "high_tension_random"
    
    # 5. 자신의 이름이 언급되면 난입
    for event in scene_context.recent_events[-3:]:
        if state.character_name in event.summary:
            return True, f"name_mentioned:{state.character_name}"
    
    return False, ""
```

---

# 4. 이모지 리액션 시스템

## 4.1 개요

유저가 캐릭터 대사에 이모지로 반응하여 **100% 정확한 감정 데이터**를 수집합니다.

## 4.2 이모지 정의

| 이모지 | 이름 | 의미 | 효과 |
|--------|------|------|------|
| ❤️ | 심쿵 | 좋아/설렘 | intimacy +0.3, joy_peaks +1 |
| 💢 | 짜증 | 화남/불쾌 | anger_peaks +1, 트리거 후보 등록 |
| 🔥 | 열광 | 흥분/재밌음 | excitement_peaks +1 |
| ⭐ | 기억해! | 이 순간 저장 | 핵심 기억 영구 저장 |

## 4.3 프론트엔드 수정: `static/index.html`

### HTML 추가 (메시지 템플릿)

```html
<!-- 캐릭터 메시지 말풍선 아래에 추가 -->
<div class="message character-message" data-turn-id="${turnId}" data-character-id="${characterId}">
    <div class="message-header">
        <span class="character-name">${characterName}</span>
    </div>
    <div class="message-content">
        ${messageContent}
    </div>
    
    <!-- 이모지 리액션 버튼 -->
    <div class="emoji-reactions">
        <button class="emoji-btn" data-emoji="❤️" title="심쿵">
            <span class="emoji">❤️</span>
            <span class="label">심쿵</span>
        </button>
        <button class="emoji-btn" data-emoji="💢" title="짜증">
            <span class="emoji">💢</span>
            <span class="label">짜증</span>
        </button>
        <button class="emoji-btn" data-emoji="🔥" title="열광">
            <span class="emoji">🔥</span>
            <span class="label">열광</span>
        </button>
        <button class="emoji-btn" data-emoji="⭐" title="기억해!">
            <span class="emoji">⭐</span>
            <span class="label">기억해!</span>
        </button>
    </div>
</div>
```

### CSS 추가

```css
/* 이모지 리액션 버튼 */
.emoji-reactions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    padding: 8px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.emoji-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 8px 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    opacity: 0.6;
}

.emoji-btn:hover {
    opacity: 1;
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
}

.emoji-btn .emoji {
    font-size: 20px;
}

.emoji-btn .label {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.7);
}

/* 선택된 상태 */
.emoji-btn.selected {
    opacity: 1;
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(255, 255, 255, 0.5);
}

.emoji-btn.selected[data-emoji="❤️"] {
    background: rgba(255, 100, 100, 0.2);
    border-color: #ff6b6b;
}

.emoji-btn.selected[data-emoji="💢"] {
    background: rgba(255, 150, 50, 0.2);
    border-color: #ff9632;
}

.emoji-btn.selected[data-emoji="🔥"] {
    background: rgba(255, 200, 50, 0.2);
    border-color: #ffc832;
}

.emoji-btn.selected[data-emoji="⭐"] {
    background: rgba(255, 215, 0, 0.2);
    border-color: gold;
}
```

### JavaScript 추가

```javascript
// ═══════════════════════════════════════════════════════════════
// 이모지 리액션 시스템
// ═══════════════════════════════════════════════════════════════

// 마지막 대화 정보 저장
let lastUserMessage = '';
let lastCharacterResponse = '';
let lastTurnId = '';
let lastCharacterId = '';

// 이모지 클릭 이벤트
document.addEventListener('click', async function(e) {
    const btn = e.target.closest('.emoji-btn');
    if (!btn) return;
    
    const container = btn.closest('.emoji-reactions');
    const messageDiv = btn.closest('.message');
    const emoji = btn.dataset.emoji;
    const turnId = messageDiv.dataset.turnId;
    const characterId = messageDiv.dataset.characterId;
    
    // ❤️💢🔥는 상호 배타적 (하나만 선택)
    if (['❤️', '💢', '🔥'].includes(emoji)) {
        container.querySelectorAll('.emoji-btn[data-emoji="❤️"], .emoji-btn[data-emoji="💢"], .emoji-btn[data-emoji="🔥"]')
            .forEach(b => b.classList.remove('selected'));
    }
    
    // 토글
    btn.classList.toggle('selected');
    
    // 선택된 경우만 API 호출
    if (btn.classList.contains('selected')) {
        await sendEmojiReaction(turnId, characterId, emoji);
        
        // ⭐인 경우 특별 피드백
        if (emoji === '⭐') {
            showToast('✨ 이 순간이 기억에 저장되었습니다!');
        }
    }
});

async function sendEmojiReaction(turnId, characterId, emoji) {
    try {
        const response = await fetch('/api/reaction/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                character_id: characterId,
                turn_id: turnId,
                emoji: emoji
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 관계 데이터 업데이트 (기존 UI에 반영)
            if (data.relationship_data) {
                updateRelationshipDisplay(characterId, data.relationship_data);
            }
        }
    } catch (error) {
        console.error('이모지 전송 실패:', error);
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}
```

## 4.4 백엔드 수정: `api/reaction.py`

**확인 및 보완 필요 사항:**

```python
"""
이모지 리액션 API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from db.database import get_db, get_relationship_data, update_relationship_data

router = APIRouter(prefix="/api/reaction", tags=["reaction"])


# 이모지 효과 정의
EMOJI_EFFECTS = {
    "❤️": {
        "emotion": "joy",
        "intimacy_delta": 0.3,
        "stat_key": "joy_peaks",
        "save_memory": False
    },
    "💢": {
        "emotion": "anger",
        "intimacy_delta": 0.0,
        "stat_key": "anger_peaks",
        "save_memory": False,
        "register_trigger": True  # 트리거 후보 등록
    },
    "🔥": {
        "emotion": "excitement",
        "intimacy_delta": 0.1,
        "stat_key": "excitement_peaks",
        "save_memory": False
    },
    "⭐": {
        "emotion": None,
        "intimacy_delta": 0.0,
        "stat_key": None,
        "save_memory": True  # 핵심 기억 저장
    }
}


class EmojiReactionRequest(BaseModel):
    user_id: str
    character_id: str
    turn_id: str
    emoji: str


class EmojiReactionResponse(BaseModel):
    success: bool
    message: str
    relationship_data: dict = None


@router.post("/", response_model=EmojiReactionResponse)
async def send_emoji_reaction(
    request: EmojiReactionRequest,
    db: Session = Depends(get_db)
):
    """
    이모지 리액션 전송
    """
    emoji = request.emoji
    
    if emoji not in EMOJI_EFFECTS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 이모지: {emoji}")
    
    effect = EMOJI_EFFECTS[emoji]
    
    # 관계 데이터 조회
    rel_data = get_relationship_data(request.user_id, request.character_id, db)
    if not rel_data:
        # 새로 생성
        rel_data = create_relationship_data(request.user_id, request.character_id, db)
    
    # 친밀도 업데이트
    if effect["intimacy_delta"]:
        rel_data.intimacy = min(10.0, rel_data.intimacy + effect["intimacy_delta"])
    
    # 감정 통계 업데이트
    if effect["stat_key"]:
        stats = rel_data.emotional_stats or {}
        stats[effect["stat_key"]] = stats.get(effect["stat_key"], 0) + 1
        rel_data.emotional_stats = stats
    
    # 핵심 기억 저장 (⭐)
    if effect["save_memory"]:
        # TODO: 현재 대화 내용을 핵심 기억으로 저장
        memory = {
            "turn_id": request.turn_id,
            "timestamp": datetime.now().isoformat(),
            "user_marked": True
        }
        memories = rel_data.core_memories or []
        memories.append(memory)
        # 최대 20개 유지
        if len(memories) > 20:
            memories = memories[-20:]
        rel_data.core_memories = memories
    
    # 트리거 후보 등록 (💢)
    if effect.get("register_trigger"):
        # TODO: 캐릭터 대사에서 키워드 추출하여 트리거 후보 등록
        pass
    
    # DB 저장
    db.commit()
    
    return EmojiReactionResponse(
        success=True,
        message=f"{emoji} 반응이 기록되었습니다!",
        relationship_data={
            "intimacy": rel_data.intimacy,
            "dominance": rel_data.dominance_score,
            "emotional_stats": rel_data.emotional_stats,
            "core_memories_count": len(rel_data.core_memories or [])
        }
    )
```

---

# 5. 유저 프로필 시스템

## 5.1 개요

유저(주인공)의 정보를 저장하여 캐릭터들이 유저를 기억하고 개인화된 반응을 합니다.

## 5.2 새 파일 생성: `models/user_profile.py`

```python
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
    key_events: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


class UserAction(BaseModel):
    """유저의 주요 행동 기록"""
    action: str
    location: str
    involved_characters: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """유저 프로필"""
    user_id: str
    
    # 기본 정보
    nickname: Optional[str] = None       # "카카시"
    gender: Optional[str] = None
    
    # 능력 정보
    ability_name: Optional[str] = None           # "치도리"
    ability_description: Optional[str] = None
    ability_rank: Optional[str] = None           # D, C, B, A, S, SS
    
    # 성격 특성 (대화에서 자동 추출)
    personality_traits: List[str] = Field(default_factory=list)
    speech_style: Optional[str] = None
    
    # 캐릭터별 인상
    character_impressions: Dict[str, CharacterImpression] = Field(default_factory=dict)
    
    # 행동 히스토리
    key_actions: List[UserAction] = Field(default_factory=list)
    mentioned_facts: List[str] = Field(default_factory=list)
    
    # 통계
    total_turns: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_action(self, action: str, location: str, characters: List[str] = None):
        """주요 행동 추가"""
        self.key_actions.append(UserAction(
            action=action,
            location=location,
            involved_characters=characters or []
        ))
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
            if len(imp.key_events) > 10:
                imp.key_events = imp.key_events[-10:]
        imp.last_updated = datetime.now()
        self.updated_at = datetime.now()
    
    def to_prompt_context(self) -> str:
        """프롬프트에 주입할 유저 정보"""
        context = f"""
[유저(주인공) 정보]
- 이름: {self.nickname or "알 수 없음"}
- 능력: {self.ability_name or "알 수 없음"} ({self.ability_rank or "등급 미정"})
"""
        if self.ability_description:
            context += f"  └ {self.ability_description}\n"
        if self.personality_traits:
            context += f"- 성격: {', '.join(self.personality_traits)}\n"
        if self.key_actions:
            recent = [a.action for a in self.key_actions[-3:]]
            context += f"- 최근 행동: {', '.join(recent)}\n"
        return context
```

## 5.3 새 파일 생성: `db/user_db.py`

```python
"""
유저 프로필 DB
"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.orm import Session

from db.database import Base, engine


class UserProfileTable(Base):
    """유저 프로필 테이블"""
    __tablename__ = "user_profiles"
    
    user_id = Column(String, primary_key=True)
    nickname = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    
    ability_name = Column(String, nullable=True)
    ability_description = Column(Text, nullable=True)
    ability_rank = Column(String, nullable=True)
    
    personality_traits = Column(Text, default="[]")  # JSON
    speech_style = Column(String, nullable=True)
    
    character_impressions = Column(Text, default="{}")  # JSON
    key_actions = Column(Text, default="[]")  # JSON
    mentioned_facts = Column(Text, default="[]")  # JSON
    
    total_turns = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_user_db():
    """유저 프로필 테이블 생성"""
    Base.metadata.create_all(bind=engine)


def get_user_profile(user_id: str, db: Session) -> Optional[dict]:
    """유저 프로필 조회"""
    profile = db.query(UserProfileTable).filter(
        UserProfileTable.user_id == user_id
    ).first()
    
    if not profile:
        return None
    
    return {
        "user_id": profile.user_id,
        "nickname": profile.nickname,
        "gender": profile.gender,
        "ability_name": profile.ability_name,
        "ability_description": profile.ability_description,
        "ability_rank": profile.ability_rank,
        "personality_traits": json.loads(profile.personality_traits or "[]"),
        "speech_style": profile.speech_style,
        "character_impressions": json.loads(profile.character_impressions or "{}"),
        "key_actions": json.loads(profile.key_actions or "[]"),
        "mentioned_facts": json.loads(profile.mentioned_facts or "[]"),
        "total_turns": profile.total_turns
    }


def create_user_profile(user_id: str, db: Session, **kwargs) -> dict:
    """유저 프로필 생성"""
    profile = UserProfileTable(
        user_id=user_id,
        **kwargs
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return get_user_profile(user_id, db)


def update_user_profile(user_id: str, db: Session, **kwargs) -> Optional[dict]:
    """유저 프로필 업데이트"""
    profile = db.query(UserProfileTable).filter(
        UserProfileTable.user_id == user_id
    ).first()
    
    if not profile:
        return None
    
    for key, value in kwargs.items():
        if hasattr(profile, key):
            if key in ["personality_traits", "key_actions", "mentioned_facts", "character_impressions"]:
                setattr(profile, key, json.dumps(value, ensure_ascii=False))
            else:
                setattr(profile, key, value)
    
    db.commit()
    return get_user_profile(user_id, db)
```

## 5.4 새 파일 생성: `api/user_api.py`

```python
"""
유저 프로필 API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from db.database import get_db
from db.user_db import get_user_profile, create_user_profile, update_user_profile

router = APIRouter(prefix="/api/user", tags=["user"])


class UserProfileResponse(BaseModel):
    success: bool
    profile: dict = None


class UserProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    ability_name: Optional[str] = None
    ability_description: Optional[str] = None
    ability_rank: Optional[str] = None


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: str, db: Session = Depends(get_db)):
    """유저 프로필 조회"""
    profile = get_user_profile(user_id, db)
    
    if not profile:
        # 없으면 새로 생성
        profile = create_user_profile(user_id, db)
    
    return UserProfileResponse(success=True, profile=profile)


@router.put("/profile/{user_id}", response_model=UserProfileResponse)
async def update_profile(
    user_id: str,
    request: UserProfileUpdateRequest,
    db: Session = Depends(get_db)
):
    """유저 프로필 업데이트"""
    profile = get_user_profile(user_id, db)
    
    if not profile:
        profile = create_user_profile(user_id, db, **request.dict(exclude_none=True))
    else:
        profile = update_user_profile(user_id, db, **request.dict(exclude_none=True))
    
    return UserProfileResponse(success=True, profile=profile)
```

---

# 6. 캐릭터 속마음 시스템

## 6.1 개요

캐릭터의 **겉으로 한 말**과 **속마음(내면의 생각)**을 분리하여 표시합니다.

## 6.2 새 파일 생성: `models/inner_thought.py`

```python
"""
캐릭터 속마음 모델
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class InnerThought(BaseModel):
    """캐릭터 속마음"""
    
    character_id: str
    character_name: str
    turn_id: str
    
    # 속마음 내용
    thought: str                       # "뭐야, 이놈? 눈빛이 예사롭지 않네."
    
    # 감정 분석
    surface_emotion: str               # 겉 감정 ("허세", "냉정")
    inner_emotion: str                 # 속 감정 ("긴장", "호기심")
    emotion_gap: bool = False          # 겉과 속이 다른지
    
    # 유저 평가
    user_evaluation: Optional[str] = None  # "만만해 보이지만 경계 필요"
    
    # 의도
    intention: Optional[str] = None    # "기선제압하려 함"
    
    timestamp: datetime = Field(default_factory=datetime.now)


# 속마음 생성 프롬프트
INNER_THOUGHT_PROMPT = """
[캐릭터]
이름: {character_name}
성격: {character_personality}
유저와의 관계: {relationship_status}

[방금 한 말]
"{character_dialogue}"

[유저의 이전 행동]
{user_context}

[요청]
{character_name}의 속마음을 JSON으로 작성하세요:

{{
  "thought": "속마음 (1~2문장)",
  "surface_emotion": "겉 감정",
  "inner_emotion": "속 감정",
  "emotion_gap": true/false,
  "user_evaluation": "유저 평가",
  "intention": "의도"
}}
"""
```

## 6.3 API 응답에 속마음 포함

`api/chat_multi.py` 응답 구조 수정:

```python
# 기존 응답에 inner_thought 추가
response = {
    "turn_id": turn_id,
    "character_id": character_id,
    "character_name": character_name,
    "message": character_response,
    "action": action_description,
    
    # 속마음 추가
    "inner_thought": {
        "thought": "저딴 놈이 감히... 두고 봐야겠어.",
        "surface_emotion": "분노",
        "inner_emotion": "불안",
        "emotion_gap": True,
        "user_evaluation": "하찮은 존재. 하지만 뒷배경 주의.",
        "intention": "기선제압"
    },
    
    "relationship_data": { ... },
    "scene_context": { ... }
}
```

## 6.4 프론트엔드: 속마음 토글 UI

```html
<!-- 캐릭터 메시지 아래에 추가 -->
<div class="inner-thought-toggle">
    <button class="toggle-btn" onclick="toggleInnerThought(this)">
        💭 속마음 보기
    </button>
</div>

<div class="inner-thought-panel" style="display: none;">
    <div class="thought-content">
        <p class="thought-text">"${innerThought.thought}"</p>
        <div class="emotion-analysis">
            <span class="surface">겉: ${innerThought.surface_emotion}</span>
            <span class="inner">(속: ${innerThought.inner_emotion})</span>
        </div>
        <p class="user-eval">평가: ${innerThought.user_evaluation}</p>
    </div>
</div>
```

```css
.inner-thought-toggle {
    margin-top: 8px;
}

.toggle-btn {
    background: transparent;
    border: 1px dashed rgba(255, 255, 255, 0.3);
    color: rgba(255, 255, 255, 0.6);
    padding: 4px 12px;
    border-radius: 16px;
    cursor: pointer;
    font-size: 12px;
}

.toggle-btn:hover {
    border-color: rgba(255, 255, 255, 0.5);
    color: rgba(255, 255, 255, 0.8);
}

.inner-thought-panel {
    background: rgba(0, 0, 0, 0.3);
    border-left: 3px solid #666;
    margin-top: 8px;
    padding: 12px;
    border-radius: 8px;
}

.thought-text {
    color: #aaa;
    font-style: italic;
    margin-bottom: 8px;
}

.emotion-analysis {
    font-size: 12px;
    color: #888;
}

.surface {
    color: #ff9999;
}

.inner {
    color: #99ccff;
    margin-left: 8px;
}

.user-eval {
    font-size: 11px;
    color: #777;
    margin-top: 8px;
}
```

```javascript
function toggleInnerThought(btn) {
    const panel = btn.closest('.message').querySelector('.inner-thought-panel');
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        btn.textContent = '💭 속마음 숨기기';
    } else {
        panel.style.display = 'none';
        btn.textContent = '💭 속마음 보기';
    }
}
```

---

# 7. Scene Dashboard UI

## 7.1 개요

**현재 상황 패널**을 추가하여 모든 캐릭터의 상태와 속마음을 한눈에 확인합니다.

## 7.2 HTML 추가

```html
<!-- 채팅 영역 옆 또는 상단에 추가 -->
<div class="scene-dashboard" id="sceneDashboard">
    <div class="dashboard-header">
        <h3>🎭 현재 상황</h3>
        <span class="location-badge" id="currentLocation">📍 베타 동 로비</span>
        <div class="tension-bar">
            <span>긴장도:</span>
            <div class="bar-container">
                <div class="bar-fill" id="tensionFill" style="width: 70%;"></div>
            </div>
        </div>
    </div>
    
    <div class="story-summary" id="storySummary">
        <h4>📖 스토리 요약</h4>
        <p>빌런과 신입 카카시가 베타 동에 도착. 주창윤과 충돌 후 황인하가 끼어들어 상황이 복잡해짐.</p>
    </div>
    
    <div class="character-states" id="characterStates">
        <h4>👥 캐릭터 상태</h4>
        
        <!-- 캐릭터 상태 카드 (동적 생성) -->
        <div class="char-state-card recent" data-char-id="npc_joo_changyun">
            <div class="char-header">
                <span class="char-mood">😤</span>
                <span class="char-name">주창윤</span>
                <span class="char-attention">[유저 주시 중]</span>
                <span class="recent-badge">● recent</span>
            </div>
            <div class="char-thought">
                💭 "저딴 놈이 감히... 두고 봐야겠어"
            </div>
        </div>
        
        <div class="char-state-card recent" data-char-id="npc_hwang_inha">
            <div class="char-header">
                <span class="char-mood">😏</span>
                <span class="char-name">황인하</span>
                <span class="char-attention">[유저 주시 중]</span>
                <span class="recent-badge">● recent</span>
            </div>
            <div class="char-thought">
                💭 "재미있는 신입이네. 좀 더 지켜볼까"
            </div>
        </div>
        
        <div class="char-state-card inactive" data-char-id="npc_min_arum">
            <div class="char-header">
                <span class="char-mood">😴</span>
                <span class="char-name">민아름</span>
                <span class="char-attention">[관심 없음]</span>
            </div>
            <div class="char-thought">
                💭 "시끄러워... 자고 싶어..."
            </div>
        </div>
        
    </div>
    
    <div class="current-focus" id="currentFocus">
        <span>🎯 현재 대화:</span>
        <strong>유저 ↔ 황인하</strong>
    </div>
</div>
```

## 7.3 CSS 추가

```css
.scene-dashboard {
    background: rgba(0, 0, 0, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    max-height: 400px;
    overflow-y: auto;
}

.dashboard-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.dashboard-header h3 {
    margin: 0;
    font-size: 16px;
}

.location-badge {
    background: rgba(255, 255, 255, 0.1);
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
}

.tension-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
}

.bar-container {
    width: 100px;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #FFC107, #F44336);
    transition: width 0.3s ease;
}

.story-summary {
    background: rgba(255, 255, 255, 0.05);
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.story-summary h4 {
    margin: 0 0 8px 0;
    font-size: 13px;
    color: #aaa;
}

.story-summary p {
    margin: 0;
    font-size: 12px;
    color: #888;
    line-height: 1.5;
}

.character-states h4 {
    margin: 0 0 12px 0;
    font-size: 13px;
    color: #aaa;
}

.char-state-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    transition: all 0.2s ease;
}

.char-state-card.recent {
    border-color: rgba(100, 200, 255, 0.3);
    background: rgba(100, 200, 255, 0.05);
}

.char-state-card.inactive {
    opacity: 0.5;
}

.char-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}

.char-mood {
    font-size: 18px;
}

.char-name {
    font-weight: bold;
    font-size: 13px;
}

.char-attention {
    font-size: 11px;
    color: #888;
}

.recent-badge {
    font-size: 10px;
    color: #64c8ff;
    margin-left: auto;
}

.char-thought {
    font-size: 11px;
    color: #777;
    font-style: italic;
    padding-left: 26px;
}

.current-focus {
    background: rgba(255, 215, 0, 0.1);
    border: 1px solid rgba(255, 215, 0, 0.3);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    text-align: center;
    margin-top: 12px;
}

.current-focus strong {
    color: gold;
}
```

## 7.4 JavaScript: Scene Dashboard 업데이트

```javascript
// Scene Dashboard 업데이트 함수
function updateSceneDashboard(sceneContext) {
    if (!sceneContext) return;
    
    // 장소
    document.getElementById('currentLocation').textContent = 
        `📍 ${sceneContext.location}`;
    
    // 긴장도
    const tensionPercent = sceneContext.tension_level * 10;
    document.getElementById('tensionFill').style.width = `${tensionPercent}%`;
    
    // 스토리 요약
    if (sceneContext.story_arc && sceneContext.story_arc.length > 0) {
        const recentStory = sceneContext.story_arc.slice(-3).join(' → ');
        document.querySelector('#storySummary p').textContent = recentStory;
    }
    
    // 캐릭터 상태
    const charStatesContainer = document.getElementById('characterStates');
    const existingCards = charStatesContainer.querySelectorAll('.char-state-card');
    existingCards.forEach(card => card.remove());
    
    for (const [charId, state] of Object.entries(sceneContext.character_states)) {
        const card = createCharacterStateCard(charId, state);
        charStatesContainer.appendChild(card);
    }
    
    // 현재 포커스
    document.querySelector('#currentFocus strong').textContent = 
        sceneContext.current_focus || '대화 없음';
}

function createCharacterStateCard(charId, state) {
    const card = document.createElement('div');
    card.className = `char-state-card ${state.recent ? 'recent' : ''} ${state.attention === 'none' ? 'inactive' : ''}`;
    card.dataset.charId = charId;
    
    const moodEmoji = getMoodEmoji(state.current_mood);
    const attentionText = getAttentionText(state.attention, state.attention_target);
    
    card.innerHTML = `
        <div class="char-header">
            <span class="char-mood">${moodEmoji}</span>
            <span class="char-name">${state.character_name}</span>
            <span class="char-attention">[${attentionText}]</span>
            ${state.recent ? '<span class="recent-badge">● recent</span>' : ''}
        </div>
        <div class="char-thought">
            💭 "${state.inner_thought || '...'}"
        </div>
    `;
    
    return card;
}

function getMoodEmoji(mood) {
    const moodMap = {
        'angry': '😤',
        'annoyed': '😒',
        'amused': '😏',
        'happy': '😊',
        'sad': '😢',
        'sleepy': '😴',
        'nervous': '😰',
        'neutral': '😐',
        'curious': '🤔',
        'hostile': '😠'
    };
    return moodMap[mood] || '😐';
}

function getAttentionText(attention, target) {
    if (attention === 'user') return '유저 주시 중';
    if (attention === 'character') return `${target} 주시 중`;
    if (attention === 'observing') return '상황 관찰 중';
    if (attention === 'none') return '관심 없음';
    return '알 수 없음';
}
```

---

# 8. API 수정 사항

## 8.1 `api/chat_multi.py` 수정

### 주요 변경 사항

1. **Scene Context 연동**
2. **Speaker Selector v2 사용**
3. **속마음 생성 추가**
4. **응답에 scene_context 포함**

```python
# chat_multi.py 수정 예시

from core.scene_manager import scene_manager
from core.speaker_selector import select_speaker_v2
from models.inner_thought import INNER_THOUGHT_PROMPT

@router.post("/location/{location_id}")
async def chat_multi(
    location_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    # 1. Scene Context 조회 또는 생성
    characters = get_characters_by_location(location_id, db)
    context = scene_manager.get_or_create_context(
        request.session_id,
        location_id,
        [{"id": c.id, "name": c.name} for c in characters]
    )
    
    # 2. 화자 선택 (개선된 버전)
    speaker_id, speaker_name, reason = select_speaker_v2(
        request.message,
        [{"id": c.id, "name": c.name} for c in characters],
        context
    )
    
    # 3. 프롬프트 생성 (Scene Context 포함)
    prompt = build_prompt_with_context(
        character=get_character(speaker_id, db),
        user_message=request.message,
        scene_context=context,
        user_profile=get_user_profile(request.user_id, db)
    )
    
    # 4. AI 응답 생성
    response = await generate_response(prompt)
    
    # 5. 속마음 생성
    inner_thought = await generate_inner_thought(
        character=get_character(speaker_id, db),
        dialogue=response,
        context=context
    )
    
    # 6. Scene Context 업데이트
    scene_manager.process_character_response(
        request.session_id,
        speaker_id,
        speaker_name,
        response,
        target="user",
        inner_thought=inner_thought.get("thought")
    )
    
    # 7. 응답 반환
    return {
        "turn_id": f"turn_{context.total_turns}",
        "character_id": speaker_id,
        "character_name": speaker_name,
        "message": response,
        "selection_reason": reason,
        "inner_thought": inner_thought,
        "scene_context": {
            "location": context.location,
            "tension_level": context.tension_level,
            "current_focus": context.current_focus,
            "story_arc": context.story_arc[-5:],
            "character_states": {
                char_id: {
                    "character_name": state.character_name,
                    "recent": state.recent,
                    "attention": state.attention.value,
                    "current_mood": state.current_mood,
                    "inner_thought": state.inner_thought
                }
                for char_id, state in context.character_states.items()
            }
        }
    }
```

## 8.2 `main.py` 수정

```python
# 라우터 추가
from api.user_api import router as user_router
from db.user_db import init_user_db

app.include_router(user_router)

@app.on_event("startup")
async def startup_event():
    init_db()
    init_character_db()
    init_user_db()  # 추가
```

---

# 9. 개발 우선순위

## 9.1 우선순위 표

| 순위 | 기능 | 파일 | 중요도 | 난이도 |
|------|------|------|--------|--------|
| **1** | Scene Context 모델 | `models/scene_context.py` | ⭐⭐⭐⭐⭐ | 중간 |
| **2** | Speaker Selector 개선 | `core/speaker_selector.py` | ⭐⭐⭐⭐⭐ | 쉬움 |
| **3** | Scene Manager | `core/scene_manager.py` | ⭐⭐⭐⭐⭐ | 중간 |
| **4** | chat_multi.py 연동 | `api/chat_multi.py` | ⭐⭐⭐⭐⭐ | 중간 |
| **5** | 이모지 리액션 UI | `static/index.html` | ⭐⭐⭐⭐ | 쉬움 |
| **6** | 이모지 API 보완 | `api/reaction.py` | ⭐⭐⭐⭐ | 쉬움 |
| **7** | 유저 프로필 모델 | `models/user_profile.py` | ⭐⭐⭐⭐ | 쉬움 |
| **8** | 유저 프로필 DB | `db/user_db.py` | ⭐⭐⭐⭐ | 쉬움 |
| **9** | 유저 프로필 API | `api/user_api.py` | ⭐⭐⭐ | 쉬움 |
| **10** | 속마음 모델 | `models/inner_thought.py` | ⭐⭐⭐ | 쉬움 |
| **11** | Scene Dashboard UI | `static/index.html` | ⭐⭐⭐ | 중간 |

## 9.2 단계별 작업

### Phase 1: 맥락 유지 (핵심)

```
1. models/scene_context.py 생성
2. core/scene_manager.py 생성
3. core/speaker_selector.py 수정
4. api/chat_multi.py 연동
5. 테스트: "넌뭔데" → 직전 화자 응답 확인
```

### Phase 2: 이모지 시스템

```
1. static/index.html에 이모지 버튼 추가
2. api/reaction.py 보완
3. 테스트: 이모지 클릭 → 관계 데이터 업데이트 확인
```

### Phase 3: 유저 프로필

```
1. models/user_profile.py 생성
2. db/user_db.py 생성
3. api/user_api.py 생성
4. main.py에 라우터 추가
```

### Phase 4: 속마음 & Dashboard

```
1. models/inner_thought.py 생성
2. chat_multi.py에 속마음 생성 추가
3. static/index.html에 속마음 토글 추가
4. static/index.html에 Scene Dashboard 추가
```

---

# 📝 체크리스트

## 백엔드

- [ ] `models/scene_context.py` 생성
- [ ] `core/scene_manager.py` 생성
- [ ] `core/speaker_selector.py` 수정 (대명사 + recent 로직)
- [ ] `api/chat_multi.py` Scene Context 연동
- [ ] `api/reaction.py` 보완
- [ ] `models/user_profile.py` 생성
- [ ] `db/user_db.py` 생성
- [ ] `api/user_api.py` 생성
- [ ] `models/inner_thought.py` 생성
- [ ] `main.py` 라우터 추가

## 프론트엔드

- [ ] 이모지 버튼 UI 추가
- [ ] 이모지 클릭 이벤트 핸들러
- [ ] 속마음 토글 UI 추가
- [ ] Scene Dashboard 패널 추가
- [ ] Dashboard 업데이트 함수

## 테스트

- [ ] 대명사 "넌", "너" → 직전 화자 응답 확인
- [ ] 이모지 클릭 → 관계 데이터 업데이트 확인
- [ ] Scene Dashboard 캐릭터 상태 표시 확인
- [ ] 속마음 토글 동작 확인

---

> **문의사항은 언제든 말씀해주세요!** 🚀
