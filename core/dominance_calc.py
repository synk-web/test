"""
Dominance 계산
SYNK MVP - 대화에서 권력 구조(Dominance) 계산
"""
from typing import Dict
from models.relationship import RelationshipData, Dominance


def calculate_dominance_change(
    user_message: str,
    character_response: str,
    current_dominance: float
) -> float:
    """
    대화에서 Dominance 변화량 계산
    
    규칙:
    - 명령형 문장: 유저 우위 (+0.1)
    - 사과/순응: 유저 열위 (-0.1)
    - 캐릭터가 거부/반항: 캐릭터 우위 (+0.1)
    - 캐릭터가 순응: 캐릭터 열위 (-0.1)
    
    Args:
        user_message: 유저 메시지
        character_response: 캐릭터 응답
        current_dominance: 현재 dominance 점수
    
    Returns:
        변화량 (-0.2 ~ +0.2)
    """
    change = 0.0
    
    # 유저 메시지 분석
    user_lower = user_message.lower()
    
    # 명령형 패턴
    command_patterns = ["해줘", "해봐", "해", "해라", "해야", "해야지", "하세요", "해주세요"]
    if any(pattern in user_lower for pattern in command_patterns):
        change += 0.1  # 유저 우위
    
    # 사과/순응 패턴
    apology_patterns = ["미안", "죄송", "사과", "잘못", "용서", "부탁"]
    if any(pattern in user_lower for pattern in apology_patterns):
        change -= 0.1  # 유저 열위
    
    # 캐릭터 응답 분석
    char_lower = character_response.lower()
    
    # 거부/반항 패턴
    refusal_patterns = ["싫어", "안 해", "안돼", "거절", "못 해", "안 할래"]
    if any(pattern in char_lower for pattern in refusal_patterns):
        change += 0.1  # 캐릭터 우위
    
    # 순응 패턴
    compliance_patterns = ["알겠어", "할게", "해줄게", "좋아", "응", "네"]
    if any(pattern in char_lower for pattern in compliance_patterns):
        change -= 0.1  # 캐릭터 열위
    
    # 변화량 제한 (-0.2 ~ +0.2)
    change = max(-0.2, min(0.2, change))
    
    return change


def update_dominance(
    rel_data: RelationshipData,
    user_message: str,
    character_response: str
) -> RelationshipData:
    """
    Dominance 업데이트
    
    Args:
        rel_data: 관계 데이터
        user_message: 유저 메시지
        character_response: 캐릭터 응답
    
    Returns:
        업데이트된 관계 데이터
    """
    # 변화량 계산
    change = calculate_dominance_change(
        user_message,
        character_response,
        rel_data.dominance.score
    )
    
    # 새로운 점수 계산
    new_score = rel_data.dominance.score + change
    
    # 범위 제한 (-1.0 ~ 1.0)
    new_score = max(-1.0, min(1.0, new_score))
    
    # 히스토리에 추가
    new_history = rel_data.dominance.history + [new_score]
    # 최근 50개만 유지
    if len(new_history) > 50:
        new_history = new_history[-50:]
    
    # 업데이트
    rel_data.dominance.score = new_score
    rel_data.dominance.history = new_history
    
    return rel_data


def describe_dominance(score: float) -> str:
    """
    Dominance 점수 설명
    
    Args:
        score: Dominance 점수 (-1.0 ~ 1.0)
    
    Returns:
        설명 문자열
    """
    if score < -0.5:
        return "유저가 완전히 주도"
    elif score < -0.3:
        return "유저가 관계를 주도"
    elif score < 0.3:
        return "균형 잡힌 관계"
    elif score < 0.5:
        return "캐릭터가 관계를 주도"
    else:
        return "캐릭터가 완전히 주도"
