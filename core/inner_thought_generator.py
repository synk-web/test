"""
속마음 생성기
SYNK MVP - 캐릭터의 속마음(Inner Thought) 생성
"""
from typing import Optional, TYPE_CHECKING
from models.character import CharacterPersona
from models.relationship import RelationshipData
from models.inner_thought import InnerThought, INNER_THOUGHT_PROMPT
from utils.gemini_client import gemini_client
import json

if TYPE_CHECKING:
    from models.scene_context import SceneContext


async def generate_inner_thought(
    character: CharacterPersona,
    character_dialogue: str,
    user_message: str,
    relationship_data: Optional[RelationshipData],
    location: str,
    scene_context: Optional["SceneContext"] = None
) -> Optional[InnerThought]:
    """
    캐릭터의 속마음 생성
    
    Args:
        character: 캐릭터 정보
        character_dialogue: 캐릭터가 방금 한 말
        user_message: 유저 메시지
        relationship_data: 관계 데이터
        location: 현재 장소
        scene_context: 씬 컨텍스트
    
    Returns:
        InnerThought 객체 또는 None
    """
    # 관계 상태
    relationship_status = "알 수 없음"
    if relationship_data:
        if relationship_data.intimacy >= 5.0:
            relationship_status = "친밀함"
        elif relationship_data.intimacy >= 2.0:
            relationship_status = "알고 지내는 사이"
        else:
            relationship_status = "낯선 사이"
    
    # Scene Context 요약
    scene_context_str = ""
    if scene_context:
        scene_context_str = f"""
현재 상황:
- 장소: {scene_context.location}
- 분위기: {scene_context.atmosphere} (긴장도: {scene_context.tension_level}/10)
- 최근 이벤트: {', '.join([e.summary for e in scene_context.recent_events[-3:]]) if scene_context.recent_events else '없음'}
"""
    
    # 프롬프트 생성
    prompt = INNER_THOUGHT_PROMPT.format(
        character_name=character.name,
        character_personality=character.personality[:200],
        relationship_status=relationship_status,
        location=location,
        scene_context=scene_context_str,
        character_dialogue=character_dialogue,
        user_context=user_message[:200]
    )
    
    try:
        # AI로 속마음 생성
        response_text = gemini_client.generate_response(prompt)
        
        # JSON 파싱 시도
        try:
            # JSON 부분만 추출 (마크다운 코드 블록 제거)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            thought_data = json.loads(response_text)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값 사용
            thought_data = {
                "thought": response_text[:100] + "...",
                "surface_emotion": "중립",
                "inner_emotion": "중립",
                "emotion_gap": False,
                "user_evaluation": "평가 중",
                "attitude_toward_user": "중립",
                "intention": "관찰 중"
            }
        
        # InnerThought 객체 생성
        from datetime import datetime
        import uuid
        
        inner_thought = InnerThought(
            character_id=character.id,
            character_name=character.name,
            turn_id=str(uuid.uuid4()),
            thought=thought_data.get("thought", ""),
            surface_emotion=thought_data.get("surface_emotion", "중립"),
            inner_emotion=thought_data.get("inner_emotion", "중립"),
            emotion_gap=thought_data.get("emotion_gap", False),
            user_evaluation=thought_data.get("user_evaluation"),
            attitude_toward_user=thought_data.get("attitude_toward_user"),
            intention=thought_data.get("intention"),
            next_plan=thought_data.get("next_plan")
        )
        
        return inner_thought
    
    except Exception as e:
        import traceback
        print(f"⚠️ 속마음 생성 오류: {str(e)}")
        print(traceback.format_exc())
        return None
