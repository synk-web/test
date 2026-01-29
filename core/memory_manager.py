"""
기억 관리
SYNK MVP - 핵심 기억 생성 및 관리
"""
from typing import List, Optional
from models.relationship import RelationshipData, CoreMemory
from datetime import datetime


def should_create_core_memory(
    user_message: str,
    character_response: str,
    emotion: Optional[str] = None
) -> bool:
    """
    핵심 기억을 생성해야 하는지 판단
    
    조건:
    - 감정이 강한 경우 (joy, anger, excitement)
    - 특별한 키워드가 포함된 경우
    - 대화가 의미있는 경우
    
    Args:
        user_message: 유저 메시지
        character_response: 캐릭터 응답
        emotion: 감정 타입
    
    Returns:
        핵심 기억 생성 여부
    """
    # 강한 감정이 있는 경우
    if emotion in ["joy", "anger", "excitement"]:
        return True
    
    # 특별한 키워드
    special_keywords = ["약속", "비밀", "고백", "사랑", "미워", "친구", "이별", "만남"]
    message_lower = (user_message + " " + character_response).lower()
    if any(keyword in message_lower for keyword in special_keywords):
        return True
    
    # 긴 대화 (의미있는 대화)
    if len(user_message) > 30 or len(character_response) > 30:
        return True
    
    return False


def create_core_memory(
    user_message: str,
    character_response: str,
    emotion: Optional[str] = None,
    trigger_keywords: Optional[List[str]] = None
) -> CoreMemory:
    """
    핵심 기억 생성
    
    Args:
        user_message: 유저 메시지
        character_response: 캐릭터 응답
        emotion: 감정 타입
        trigger_keywords: 트리거 키워드 리스트
    
    Returns:
        핵심 기억 객체
    """
    # 기억 요약 생성 (간단한 요약)
    summary = f"유저: {user_message[:50]}{'...' if len(user_message) > 50 else ''}"
    
    # 기억에 남는 대사 (캐릭터 응답의 일부)
    memorable_quote = character_response[:100] if len(character_response) > 0 else None
    
    return CoreMemory(
        summary=summary,
        memorable_quote=memorable_quote,
        timestamp=datetime.now(),
        trigger_keywords=trigger_keywords or [],
        emotion=emotion
    )


def add_core_memory(
    rel_data: RelationshipData,
    user_message: str,
    character_response: str,
    emotion: Optional[str] = None,
    trigger_keywords: Optional[List[str]] = None
) -> RelationshipData:
    """
    핵심 기억 추가
    
    Args:
        rel_data: 관계 데이터
        user_message: 유저 메시지
        character_response: 캐릭터 응답
        emotion: 감정 타입
        trigger_keywords: 트리거 키워드 리스트
    
    Returns:
        업데이트된 관계 데이터
    """
    # 핵심 기억 생성 여부 확인
    if should_create_core_memory(user_message, character_response, emotion):
        memory = create_core_memory(
            user_message,
            character_response,
            emotion,
            trigger_keywords
        )
        
        # 기억 추가 (최대 10개 유지)
        rel_data.core_memories.append(memory)
        if len(rel_data.core_memories) > 10:
            rel_data.core_memories = rel_data.core_memories[-10:]
    
    return rel_data
