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
    """씬 상태 관리자 (싱글톤 패턴)"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SceneManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        # 세션별 씬 컨텍스트 저장
        self._contexts: Dict[str, SceneContext] = {}
        self._initialized = True
    
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
        pronouns = ["넌", "너", "니가", "네가", "당신", "니", "네", "너는", "당신은", "당신이"]
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
        inner_thought: str = None,  # 문자열 또는 dict (하위 호환성)
        mood: str = None
    ):
        """
        캐릭터 응답 처리 및 씬 컨텍스트 업데이트
        
        - response가 있으면 메인 응답자: recent=True, attention=USER
        - response가 없으면 서브/무반응: recent=False, attention=OBSERVING
        """
        context = self.get_context(session_id)
        if not context:
            return
        
        # inner_thought 처리 (dict 또는 문자열)
        inner_thought_str = None
        if inner_thought:
            if isinstance(inner_thought, dict):
                inner_thought_str = inner_thought.get("thought", "")
            else:
                inner_thought_str = inner_thought
        
        # 메인 응답자 처리 (response가 비어있지 않음)
        if response:
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
            
            # last_speaker 업데이트
            context.last_speaker_id = character_id
            context.last_speaker_name = character_name
            context.last_target = target
            
            # 캐릭터 상태 업데이트: 메인 응답자
            attention = CharacterAttention.USER if target == "user" else CharacterAttention.CHARACTER
            if character_id in context.character_states:
                state = context.character_states[character_id]
                state.attention = attention
                state.attention_target = target
                state.recent = True  # ⚠️ 메인 응답자만 recent=True
                state.inner_thought = inner_thought_str
                state.last_spoke_at = datetime.now()
                state.turn_count += 1
                if mood:
                    state.current_mood = mood
            
            # 현재 포커스 업데이트
            if target == "user":
                context.current_focus = f"유저 ↔ {character_name}"
            else:
                context.current_focus = f"{character_name} ↔ {target_name}"
        
        # 서브/무반응 처리 (response가 비어있음)
        else:
            if character_id in context.character_states:
                state = context.character_states[character_id]
                # 속마음만 업데이트
                if inner_thought_str:
                    state.inner_thought = inner_thought_str
                # recent=False 유지 (이미 reset_recent_flags에서 설정됨)
                state.recent = False
                # attention을 OBSERVING으로 설정 (NONE이 아닌 경우)
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
