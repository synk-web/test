"""
프롬프트 빌더 (캐릭터 + 관계 데이터 + Scene Context 통합)
SYNK MVP - 캐릭터 응답 생성용 컨텍스트 구성
"""
from typing import List, Dict, Optional, TYPE_CHECKING
from models.character import CharacterPersona
from models.relationship import RelationshipData
from core.dominance_calc import describe_dominance

if TYPE_CHECKING:
    from models.scene_context import SceneContext


def format_core_memories(memories: List, max_count: int = 3) -> str:
    """핵심 기억 포맷팅"""
    if not memories:
        return "없음"
    
    formatted = []
    for mem in memories[:max_count]:
        # CoreMemory 객체 또는 딕셔너리 모두 처리
        if hasattr(mem, 'summary'):
            # CoreMemory 객체
            summary = mem.summary
            quote = mem.memorable_quote
        else:
            # 딕셔너리
            summary = mem.get("summary", "") if isinstance(mem, dict) else str(mem)
            quote = mem.get("memorable_quote", "") if isinstance(mem, dict) else None
        
        if quote:
            formatted.append(f"- {summary} (\"{quote}\")")
        else:
            formatted.append(f"- {summary}")
    
    return "\n".join(formatted)


def format_triggers(triggers: List) -> str:
    """트리거 키워드 포맷팅"""
    if not triggers:
        return "없음"
    
    keywords = []
    for t in triggers[:5]:
        # TriggerKeyword 객체 또는 딕셔너리 모두 처리
        if hasattr(t, 'keyword'):
            # TriggerKeyword 객체
            keywords.append(f"'{t.keyword}'")
        else:
            # 딕셔너리
            keyword = t.get('keyword', '') if isinstance(t, dict) else str(t)
            keywords.append(f"'{keyword}'")
    
    return ", ".join(keywords)


def get_intimacy_level(intimacy: float) -> str:
    """친밀도 레벨 설명"""
    if intimacy < 1.0:
        return "모르는 사이"
    elif intimacy < 3.0:
        return "아는 사이"
    elif intimacy < 5.0:
        return "친구"
    elif intimacy < 7.0:
        return "절친"
    elif intimacy < 9.0:
        return "특별한 사이"
    else:
        return "연인"


def build_relationship_context(
    rel_data: RelationshipData, 
    character: Optional[CharacterPersona] = None
) -> str:
    """
    관계 데이터 기반 컨텍스트 프롬프트 생성
    
    Args:
        rel_data: 관계 데이터
        character: 캐릭터 정보 (감정 트리거 연동용)
    """
    
    intimacy_level = get_intimacy_level(rel_data.intimacy)
    dominance_desc = describe_dominance(rel_data.dominance.score)
    
    # 캐릭터별 트리거와 관계 데이터 트리거 병합
    all_triggers = []
    
    # 관계 데이터의 트리거 (유저가 💢 눌렀던 키워드)
    if rel_data.trigger_keywords:
        for t in rel_data.trigger_keywords:
            if hasattr(t, 'keyword'):
                all_triggers.append(t.keyword)
            elif isinstance(t, dict):
                all_triggers.append(t.get("keyword", ""))
    
    # 캐릭터 기본 트리거
    if character and character.emotion_triggers:
        all_triggers.extend(character.emotion_triggers.keys())
    
    trigger_text = ", ".join(set(all_triggers)) if all_triggers else "없음"
    
    context = f"""
[유저와의 관계]
- 관계 단계: {intimacy_level} (친밀도: {rel_data.intimacy:.1f}/10.0)
- 관계 역학: {dominance_desc} (dominance: {rel_data.dominance.score:.2f})
- 감정 히스토리: 기쁨 {rel_data.emotional_stats.joy_peaks}회, 화남 {rel_data.emotional_stats.anger_peaks}회, 열광 {rel_data.emotional_stats.excitement_peaks}회

[핵심 기억]
{format_core_memories(rel_data.core_memories[:3])}

[주의 키워드] (언급 시 강한 반응)
{trigger_text}

[응답 톤 가이드]
"""
    
    # Dominance에 따른 응답 가이드
    if rel_data.dominance.score < -0.3:
        context += "- 유저가 관계를 주도함. 더 순종적이고 부드럽게 반응하세요.\n"
    elif rel_data.dominance.score > 0.3:
        context += "- 캐릭터가 관계를 주도함. 더 당당하고 도도하게 반응하세요.\n"
    else:
        context += "- 균형 잡힌 관계. 캐릭터 본연의 성격대로 반응하세요.\n"
    
    # 친밀도에 따른 응답 가이드
    if rel_data.intimacy < 2.0:
        context += "- 아직 친하지 않음. 거리감을 유지하세요.\n"
    elif rel_data.intimacy < 5.0:
        context += "- 어느 정도 친해짐. 자연스럽게 대화하세요.\n"
    elif rel_data.intimacy < 8.0:
        context += "- 매우 친함. 편하게 대하고 농담도 가능.\n"
    else:
        context += "- 특별한 관계. 속마음을 조금씩 보여줄 수 있음.\n"
    
    # 핵심 기억 활용 가이드
    if rel_data.core_memories:
        context += "- 핵심 기억의 키워드가 나오면 자연스럽게 언급하세요.\n"
    
    return context


def build_multi_character_context(
    characters: List[CharacterPersona],
    speaking_character: CharacterPersona,
    location: str
) -> str:
    """
    멀티 캐릭터 씬용 컨텍스트
    
    Args:
        characters: 같은 장소의 모든 캐릭터
        speaking_character: 현재 말하는 캐릭터
        location: 현재 장소
    """
    
    other_chars = [c for c in characters if c.id != speaking_character.id]
    
    context = f"""
[현재 장소: {location}]

[함께 있는 인물]
"""
    
    for char in other_chars:
        context += f"- {char.name}: {char.personality[:50]}...\n"
    
    context += f"""
[당신은 '{speaking_character.name}'입니다]
- 다른 캐릭터들을 인식하고 있습니다.
- 필요하면 다른 캐릭터에게 말을 걸 수 있습니다.
- 다른 캐릭터의 대사는 쓰지 마세요. 당신의 대사만 작성하세요.
"""
    
    return context
