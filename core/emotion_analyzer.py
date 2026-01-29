"""
감정 분석
SYNK MVP - 대화에서 감정 감지 및 통계 업데이트
"""
from typing import Optional
from models.relationship import RelationshipData, EmotionalStats


def detect_emotion(message: str) -> Optional[str]:
    """
    메시지에서 감정 감지
    
    Args:
        message: 분석할 메시지
    
    Returns:
        감정 타입 (joy, anger, excitement, sadness, fear) 또는 None
    """
    message_lower = message.lower()
    
    # 기쁨 (joy)
    joy_patterns = ["좋아", "행복", "기쁘", "웃", "즐거", "신나", "재미", "최고", "사랑"]
    if any(pattern in message_lower for pattern in joy_patterns):
        return "joy"
    
    # 화남 (anger)
    anger_patterns = ["화나", "짜증", "미워", "싫어", "혐오", "빡쳐", "열받", "분노", "욕"]
    if any(pattern in message_lower for pattern in anger_patterns):
        return "anger"
    
    # 열광 (excitement)
    excitement_patterns = ["대단", "멋져", "최고", "완벽", "놀라", "신기", "와", "우와", "짱"]
    if any(pattern in message_lower for pattern in excitement_patterns):
        return "excitement"
    
    # 슬픔 (sadness)
    sadness_patterns = ["슬퍼", "우울", "힘들", "아픔", "괴로", "후회", "미안", "죄송"]
    if any(pattern in message_lower for pattern in sadness_patterns):
        return "sadness"
    
    # 두려움 (fear)
    fear_patterns = ["무서", "두려", "겁", "불안", "걱정", "무섭", "무서워"]
    if any(pattern in message_lower for pattern in fear_patterns):
        return "fear"
    
    return None


def update_emotional_stats(
    rel_data: RelationshipData,
    user_message: str,
    character_response: str
) -> RelationshipData:
    """
    감정 통계 업데이트
    
    Args:
        rel_data: 관계 데이터
        user_message: 유저 메시지
        character_response: 캐릭터 응답
    
    Returns:
        업데이트된 관계 데이터
    """
    # 유저 메시지 감정 감지
    user_emotion = detect_emotion(user_message)
    if user_emotion:
        if user_emotion == "joy":
            rel_data.emotional_stats.joy_peaks += 1
        elif user_emotion == "anger":
            rel_data.emotional_stats.anger_peaks += 1
        elif user_emotion == "excitement":
            rel_data.emotional_stats.excitement_peaks += 1
        elif user_emotion == "sadness":
            rel_data.emotional_stats.sadness_peaks += 1
        elif user_emotion == "fear":
            rel_data.emotional_stats.fear_peaks += 1
    
    # 캐릭터 응답 감정 감지
    char_emotion = detect_emotion(character_response)
    if char_emotion:
        if char_emotion == "joy":
            rel_data.emotional_stats.joy_peaks += 1
        elif char_emotion == "anger":
            rel_data.emotional_stats.anger_peaks += 1
        elif char_emotion == "excitement":
            rel_data.emotional_stats.excitement_peaks += 1
        elif char_emotion == "sadness":
            rel_data.emotional_stats.sadness_peaks += 1
        elif char_emotion == "fear":
            rel_data.emotional_stats.fear_peaks += 1
    
    return rel_data
