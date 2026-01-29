"""
트리거 감지
SYNK MVP - 감정 트리거 키워드 감지 및 관리
"""
from typing import List, Optional
from models.relationship import RelationshipData, TriggerKeyword
from models.character import CharacterPersona
from datetime import datetime


def detect_trigger_keyword(
    message: str,
    character: CharacterPersona,
    existing_triggers: List[TriggerKeyword]
) -> Optional[str]:
    """
    메시지에서 트리거 키워드 감지
    
    Args:
        message: 분석할 메시지
        character: 캐릭터 정보
        existing_triggers: 기존 트리거 키워드 리스트
    
    Returns:
        감지된 키워드 또는 None
    """
    message_lower = message.lower()
    
    # 캐릭터의 기본 감정 트리거 확인
    for keyword, emotion in character.emotion_triggers.items():
        if keyword.lower() in message_lower:
            return keyword
    
    # 기존 트리거 키워드 확인
    for trigger in existing_triggers:
        if trigger.keyword.lower() in message_lower:
            return trigger.keyword
    
    return None


def update_trigger_keyword(
    rel_data: RelationshipData,
    message: str,
    character: CharacterPersona,
    emotion: Optional[str] = None
) -> RelationshipData:
    """
    트리거 키워드 업데이트
    
    Args:
        rel_data: 관계 데이터
        message: 분석할 메시지
        character: 캐릭터 정보
        emotion: 감정 타입 (리액션에서 오는 경우)
    
    Returns:
        업데이트된 관계 데이터
    """
    # 트리거 키워드 감지
    detected_keyword = detect_trigger_keyword(
        message,
        character,
        rel_data.trigger_keywords
    )
    
    if not detected_keyword:
        return rel_data
    
    # 감정 타입 결정
    if not emotion:
        # 캐릭터의 기본 트리거에서 감정 가져오기
        emotion = character.emotion_triggers.get(detected_keyword, "anger")
    
    # 기존 트리거 키워드 찾기
    existing_trigger = None
    for trigger in rel_data.trigger_keywords:
        if trigger.keyword == detected_keyword:
            existing_trigger = trigger
            break
    
    if existing_trigger:
        # 기존 트리거 업데이트
        existing_trigger.occurrence_count += 1
        # 신뢰도 증가 (최대 1.0)
        existing_trigger.confidence = min(1.0, existing_trigger.confidence + 0.1)
    else:
        # 새 트리거 생성
        new_trigger = TriggerKeyword(
            keyword=detected_keyword,
            emotion=emotion,
            occurrence_count=1,
            confidence=0.5,
            first_occurrence=datetime.now()
        )
        rel_data.trigger_keywords.append(new_trigger)
    
    # 최대 20개 유지
    if len(rel_data.trigger_keywords) > 20:
        # 신뢰도가 낮은 것부터 제거
        rel_data.trigger_keywords.sort(key=lambda x: x.confidence)
        rel_data.trigger_keywords = rel_data.trigger_keywords[-20:]
    
    return rel_data
