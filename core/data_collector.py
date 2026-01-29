"""
데이터 수집
SYNK MVP - 대화 턴에서 관계 데이터 수집 및 업데이트
"""
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from models.relationship import RelationshipData
from models.character import CharacterPersona
from db.database import get_relationship_data, update_relationship_data
from core.dominance_calc import update_dominance
from core.emotion_analyzer import update_emotional_stats, detect_emotion
from core.memory_manager import add_core_memory
from core.trigger_detector import update_trigger_keyword


async def process_turn(
    user_id: str,
    character_id: str,
    turn_data: Dict,
    emoji_reaction: Optional[str] = None,
    db: Session = None
) -> Optional[RelationshipData]:
    """
    대화 턴 처리 및 관계 데이터 업데이트
    
    Args:
        user_id: 유저 ID
        character_id: 캐릭터 ID
        turn_data: 턴 데이터
            - turn_id: 턴 ID
            - user_message: 유저 메시지
            - character_response: 캐릭터 응답
            - timestamp: 타임스탬프
        emoji_reaction: 이모지 리액션 (❤️, 💢, ⭐, 🔥 등)
        db: DB 세션
    
    Returns:
        업데이트된 관계 데이터
    """
    if not db:
        return None
    
    # 관계 데이터 가져오기
    rel_data = get_relationship_data(user_id, character_id, db)
    if not rel_data:
        return None
    
    user_message = turn_data.get("user_message", "")
    character_response = turn_data.get("character_response", "")
    
    # 캐릭터 정보 가져오기
    from db.character_db import get_character
    character = get_character(character_id, db)
    if not character:
        return None
    
    # 1. 감정 감지
    # 이모지 리액션이 있으면 AI 분석 스킵 (100% 정확한 유저 피드백)
    user_emotion = None
    char_emotion = detect_emotion(character_response)
    
    # 이모지 리액션 처리 (명세서 v2에 따라)
    if emoji_reaction:
        if emoji_reaction == "❤️":
            user_emotion = "joy"
            # intimacy +0.3, joy_peaks +1
            rel_data.intimacy = min(10.0, rel_data.intimacy + 0.3)
            rel_data.emotional_stats.joy_peaks += 1
        elif emoji_reaction == "💢":
            user_emotion = "anger"
            # anger_peaks +1, 트리거 후보 등록
            rel_data.emotional_stats.anger_peaks += 1
            # 트리거 키워드 후보 등록 (캐릭터 대사에서 명사 추출)
            # character_response에서 트리거 키워드 찾기
            rel_data = update_trigger_keyword(
                rel_data,
                character_response,  # 캐릭터 대사에서 트리거 찾기
                character,
                emotion="anger"
            )
        elif emoji_reaction == "🔥":
            user_emotion = "excitement"
            # excitement_peaks +1
            rel_data.emotional_stats.excitement_peaks += 1
        elif emoji_reaction == "⭐":
            # 핵심 기억 생성 (AI가 대화 요약 생성)
            add_core_memory(
                rel_data,
                user_message,
                character_response,
                emotion=char_emotion or "joy"
            )
    else:
        # 이모지가 없을 때만 AI 감정 분석
        user_emotion = detect_emotion(user_message)
    
    # 2. 감정 통계 업데이트 (이모지가 없을 때만)
    if not emoji_reaction:
        rel_data = update_emotional_stats(rel_data, user_message, character_response)
    
    # 3. Dominance 업데이트
    rel_data = update_dominance(rel_data, user_message, character_response)
    
    # 4. 트리거 키워드 업데이트
    rel_data = update_trigger_keyword(
        rel_data,
        user_message,
        character,
        emotion=user_emotion
    )
    
    # 5. 핵심 기억 추가
    trigger_keywords = [t.keyword for t in rel_data.trigger_keywords if t.keyword in user_message]
    rel_data = add_core_memory(
        rel_data,
        user_message,
        character_response,
        emotion=char_emotion or user_emotion,
        trigger_keywords=trigger_keywords if trigger_keywords else None
    )
    
    # 6. 친밀도 업데이트
    # 기본적으로 대화할 때마다 약간씩 증가
    intimacy_increase = 0.1
    
    # 감정에 따른 친밀도 변화
    if user_emotion == "joy" or emoji_reaction == "❤️":
        intimacy_increase += 0.2
    elif user_emotion == "anger" or emoji_reaction == "💢":
        intimacy_increase -= 0.1
    
    # Dominance에 따른 친밀도 변화
    if -0.3 <= rel_data.dominance.score <= 0.3:
        intimacy_increase += 0.1  # 균형 잡힌 관계는 친밀도 증가
    
    rel_data.intimacy = max(0.0, min(10.0, rel_data.intimacy + intimacy_increase))
    
    # 7. 총 턴 수 증가
    rel_data.total_turns += 1
    rel_data.updated_at = datetime.now()
    
    # 8. DB에 저장
    updated_rel_data = update_relationship_data(rel_data, db)
    
    return updated_rel_data
