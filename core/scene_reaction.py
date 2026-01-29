"""
씬 리액션 시스템
여러 캐릭터가 동시에/순차적으로 반응하는 시스템
"""
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from models.character import CharacterPersona
from models.scene_context import SceneContext, CharacterAttention
from utils.gemini_client import gemini_client
from core.prompt_builder_v2 import build_relationship_context, build_multi_character_context
from core.inner_thought_generator import generate_inner_thought
# build_conversation_context는 더 이상 사용하지 않음
from db.database import get_relationship_data
from sqlalchemy.orm import Session


class MainResponse(BaseModel):
    """메인 응답 (긴 대사)"""
    character_id: str
    character_name: str
    message: str
    action: Optional[str] = None  # *행동 묘사*
    inner_thought: Optional[dict] = None  # InnerThought 객체를 dict로 변환


class SubReaction(BaseModel):
    """서브 리액션 (짧은 반응)"""
    character_id: str
    character_name: str
    reaction: str  # 짧은 반응: "크큭...", "*코웃음*", "흥..."
    inner_thought: Optional[dict] = None  # InnerThought 객체를 dict로 변환


class SceneReactionResult(BaseModel):
    """씬 리액션 결과"""
    main_responses: List[MainResponse]  # 메인 응답자들 (제한 없음)
    sub_reactions: List[SubReaction]  # 서브 리액션 (나머지)
    no_reaction: List[Dict]  # 무반응 캐릭터 (속마음만)


# ═══════════════════════════════════════════════════════════════
# 반응 범위 분석
# ═══════════════════════════════════════════════════════════════

FULL_REACTION_TRIGGERS = [
    "모두", "다들", "여기 있는 사람들", "전부",
    "너희들", "니들", "야 다들", "모두에게", "다들에게"
]

GROUP_REACTION_TRIGGERS = {
    "남자들": ["남자", "남성", "형들"],
    "여자들": ["여자", "여성", "언니들"],
}


def analyze_reaction_scope(user_message: str) -> str:
    """
    반응 범위 분석
    
    Returns:
        "all" - 모두 반응
        "group" - 특정 그룹만 반응
        "selective" - 선택적 반응 (기본)
    """
    user_msg_lower = user_message.lower()
    
    for trigger in FULL_REACTION_TRIGGERS:
        if trigger in user_msg_lower:
            return "all"
    
    for group, keywords in GROUP_REACTION_TRIGGERS.items():
        for keyword in keywords:
            if keyword in user_msg_lower:
                return group
    
    return "selective"


# ═══════════════════════════════════════════════════════════════
# 직접 호명 감지
# ═══════════════════════════════════════════════════════════════

def is_directly_mentioned(character: CharacterPersona, user_message: str) -> bool:
    """캐릭터가 직접 호명되었는지 확인"""
    user_msg_lower = user_message.lower()
    char_name = character.name
    
    # 정확한 이름 매칭
    if char_name in user_message or char_name.lower() in user_msg_lower:
        return True
    
    # 이름 변형 (성 제외, 이름만)
    if len(char_name) >= 2:
        first_name = char_name[-2:]  # 마지막 2글자 (이름)
        name_variations = [
            first_name,           # 인하
            first_name + "야",    # 인하야
            first_name + "아",    # 인하아
            first_name + "씨",    # 인하씨
        ]
        for variation in name_variations:
            if variation in user_message:
                return True
    
    return False


# ═══════════════════════════════════════════════════════════════
# 캐릭터별 반응 타입 결정
# ═══════════════════════════════════════════════════════════════

def determine_reaction_type(
    character: CharacterPersona,
    character_id: str,
    scene_context: Optional[SceneContext],
    user_message: str,
    reaction_scope: str,
    directly_mentioned: bool = False
) -> str:
    """
    캐릭터별 반응 타입 결정
    
    Returns:
        "main" - 메인 응답자 (긴 대사)
        "reaction" - 서브 리액션 (짧은 반응)
        "ignore" - 무반응 (속마음만)
    """
    # 1. 직접 호명되면 무조건 main
    if directly_mentioned:
        return "main"
    
    # 2. "모두" 트리거면 전원 reaction 이상
    if reaction_scope == "all":
        # 최근 대화 참여자는 main (제한 없음)
        if scene_context and character_id in scene_context.character_states:
            state = scene_context.character_states[character_id]
            if state.recent:
                return "main"
        # 나머지는 reaction
        return "reaction"
    
    # 3. selective 범위에서 recent 캐릭터는 main (제한 없음)
    if reaction_scope == "selective":
        if scene_context and character_id in scene_context.character_states:
            state = scene_context.character_states[character_id]
            if state.recent:
                return "main"
    
    # 4. 캐릭터 성격에 따른 반응
    if scene_context and character_id in scene_context.character_states:
        state = scene_context.character_states[character_id]
        if state.attention == CharacterAttention.NONE:
            return "ignore"  # 관심 없음
    
    # 5. 기본값: reaction (생각란에만 표시)
    return "reaction"


# ═══════════════════════════════════════════════════════════════
# 메인 응답 생성
# ═══════════════════════════════════════════════════════════════

async def generate_main_response(
    character: CharacterPersona,
    user_message: str,
    scene_context: Optional[SceneContext],
    characters: List[CharacterPersona],
    location: str,
    conversation_history: List[Dict],
    relationship_data,
    user_id: str,
    recent_story_summaries: List[Dict] = None
) -> MainResponse:
    """메인 응답 생성 (긴 대사)"""
    
    # 프롬프트 구성
    relationship_context = build_relationship_context(relationship_data)
    multi_context = build_multi_character_context(
        characters=[c for c in characters if c.id != character.id],
        speaking_character=character,
        location=location
    )
    # conversation_history가 List[Dict]인 경우 간단한 문자열로 변환
    if isinstance(conversation_history, list):
        conversation_context = "\n".join([
            f"{turn.get('character_name', turn.get('speaker', '유저'))}: {turn.get('message', '')}"
            for turn in conversation_history[-5:]
        ])
    else:
        conversation_context = ""
    
    # 스토리 컨텍스트 추가 (기억력 향상)
    story_context = ""
    if recent_story_summaries:
        from core.story_analyzer import build_story_context_for_prompt
        story_context = build_story_context_for_prompt(recent_story_summaries)
    
    # Scene Context 요약
    scene_summary = ""
    if scene_context:
        scene_summary = f"""
[현재 씬 상태]
- 분위기: {scene_context.atmosphere} (긴장도: {scene_context.tension_level}/10)
- 마지막 화자: {scene_context.last_speaker_name or '없음'}
- 최근 이벤트: {', '.join([e.summary for e in scene_context.recent_events[-3:]]) if scene_context.recent_events else '없음'}
"""
    
    prompt = f"""
당신은 '{character.name}'입니다.

[캐릭터 정보]
{character.personality[:500]}

[관계 데이터]
{relationship_context}

{story_context}

{scene_summary}

{multi_context}

{conversation_context}

[현재 대화]
유저: {user_message}

[⚠️ 매우 중요한 지시사항]

1. **스토리 컨텍스트 활용 (필수)**
   - 위의 "[📖 최근 스토리 흐름]"을 반드시 참고하세요.
   - 이전 대화에서 일어난 사건들을 기억하고 일관성 있게 응답하세요.
   - 예를 들어, 이전에 유저가 주창윤의 팔목을 잡았다면, 그 사건을 언급하거나 반응할 수 있습니다.
   - 스토리 흐름을 무시하지 마세요!

2. **유저 집중 (필수)**
   - 유저가 당신에게 직접 말을 걸었습니다. 다음을 **반드시** 따르세요:
   - 유저에게 직접 응답하세요. 유저를 소외시키지 마세요.
   - 다른 캐릭터를 언급할 수 있지만, 반드시 유저에게도 말을 걸어야 합니다.
   - 유저의 질문이나 말에 정확히 답하세요.
   - **응답의 대부분(70% 이상)은 유저에게 직접 말을 걸어야 합니다.**

[응답 지침]
- 캐릭터의 말투와 성격을 100% 유지하세요.
- 다른 캐릭터들이 주변에 있다는 것을 인지하세요.
- 자연스러운 그룹 대화의 일부처럼 반응하세요.
- 이전 대화의 맥락을 활용하여 일관성 있는 응답을 하세요.
- 응답은 대사만 작성하세요. (설명이나 행동 묘사는 *별표* 안에)
"""
    
    # 응답 생성
    response_text = gemini_client.generate_response(prompt)
    
    # 속마음 생성 (객체 전체 전달)
    inner_thought_obj = None
    try:
        inner_thought_obj = await generate_inner_thought(
            character=character,
            character_dialogue=response_text,
            user_message=user_message,
            relationship_data=relationship_data,
            location=location,
            scene_context=scene_context
        )
    except Exception as e:
        print(f"⚠️ 속마음 생성 오류 ({character.name}): {str(e)}")
    
    # inner_thought 객체를 dict로 변환
    inner_thought_dict = None
    if inner_thought_obj:
        inner_thought_dict = {
            "thought": inner_thought_obj.thought,
            "surface_emotion": inner_thought_obj.surface_emotion,
            "inner_emotion": inner_thought_obj.inner_emotion,
            "emotion_gap": inner_thought_obj.emotion_gap,
            "user_evaluation": inner_thought_obj.user_evaluation,
            "attitude_toward_user": inner_thought_obj.attitude_toward_user,
            "intention": inner_thought_obj.intention
        }
    
    return MainResponse(
        character_id=character.id,
        character_name=character.name,
        message=response_text,
        inner_thought=inner_thought_dict
    )


# ═══════════════════════════════════════════════════════════════
# 서브 리액션 생성
# ═══════════════════════════════════════════════════════════════

async def generate_sub_reaction(
    character: CharacterPersona,
    character_id: str,
    user_message: str,
    main_responses: List[MainResponse],
    scene_context: Optional[SceneContext],
    relationship_data,
    location: str
) -> SubReaction:
    """서브 리액션 생성 (짧은 반응)"""
    
    # 간단한 프롬프트로 짧은 반응 생성
    main_speakers = [r.character_name for r in main_responses]
    main_text = " ".join([r.message[:50] for r in main_responses])
    
    prompt = f"""
당신은 '{character.name}'입니다.

[상황]
유저가 말했습니다: "{user_message}"
{main_speakers[0] if main_speakers else "다른 캐릭터"}가 응답했습니다: "{main_text[:100]}..."

[요청]
이 상황에 대한 **매우 짧은 반응**을 작성하세요.

[규칙]
- 1~2문장 이하로 매우 짧게
- 말투와 성격 유지
- 예시: "크큭...", "*코웃음*", "흥...", "*눈을 가늘게 뜨며*", "후후..."

[응답 형식]
대사만 작성하세요. 행동 묘사는 *별표* 안에.
"""
    
    reaction_text = gemini_client.generate_response(prompt)
    
    # 속마음 생성 (객체 전체 전달)
    inner_thought_obj = None
    try:
        inner_thought_obj = await generate_inner_thought(
            character=character,
            character_dialogue=reaction_text,
            user_message=user_message,
            relationship_data=relationship_data,
            location=location,
            scene_context=scene_context
        )
    except Exception as e:
        print(f"⚠️ 속마음 생성 오류 ({character.name}): {str(e)}")
    
    # inner_thought 객체를 dict로 변환
    inner_thought_dict = None
    if inner_thought_obj:
        inner_thought_dict = {
            "thought": inner_thought_obj.thought,
            "surface_emotion": inner_thought_obj.surface_emotion,
            "inner_emotion": inner_thought_obj.inner_emotion,
            "emotion_gap": inner_thought_obj.emotion_gap,
            "user_evaluation": inner_thought_obj.user_evaluation,
            "attitude_toward_user": inner_thought_obj.attitude_toward_user,
            "intention": inner_thought_obj.intention
        }
    
    return SubReaction(
        character_id=character.id,
        character_name=character.name,
        reaction=reaction_text,
        inner_thought=inner_thought_dict
    )


# ═══════════════════════════════════════════════════════════════
# 끼어들기 응답 생성
# ═══════════════════════════════════════════════════════════════

async def generate_intervention_response(
    character: CharacterPersona,
    user_message: str,
    main_responses: List[MainResponse],
    scene_context: Optional[SceneContext],
    characters: List[CharacterPersona],
    location: str,
    relationship_data,
    recent_story_summaries: List[Dict] = None
) -> Optional[MainResponse]:
    """끼어들기 응답 생성 (캐릭터가 대화에 끼어드는 경우)"""
    
    # 메인 응답자들의 대사 요약
    main_dialogue = "\n".join([
        f"{r.character_name}: {r.message[:100]}..." 
        for r in main_responses
    ])
    
    # 스토리 컨텍스트 추가
    story_context = ""
    if recent_story_summaries:
        from core.story_analyzer import build_story_context_for_prompt
        story_context = build_story_context_for_prompt(recent_story_summaries)
    
    prompt = f"""
당신은 '{character.name}'입니다.

[캐릭터 정보]
{character.personality[:400]}

{story_context}

[현재 상황]
장소: {location}
유저가 말했습니다: "{user_message}"

다른 캐릭터들이 응답했습니다:
{main_dialogue}

[⚠️ 중요 지시사항]
1. **스토리 컨텍스트 활용**: 위의 "[📖 최근 스토리 흐름]"을 참고하여 이전 대화의 맥락을 활용하세요.
2. **일관성 유지**: 이전 대화에서 일어난 사건들을 기억하고 일관성 있게 응답하세요.

[요청]
당신은 이 대화에 **끼어들고** 싶습니다.
캐릭터의 성격에 맞게 자연스럽게 끼어드는 대사를 작성하세요.

[규칙]
- 캐릭터의 말투와 성격을 100% 유지
- 끼어드는 것처럼 자연스럽게 (예: "*끼어들며*", "*옆에서*", "*비웃으며*")
- 2~4문장 정도
- 유저에게도 말을 걸어야 함
- 이전 대화의 맥락을 활용하여 일관성 있는 응답을 하세요

[응답 형식]
대사만 작성하세요. 행동 묘사는 *별표* 안에.
"""
    
    try:
        response_text = gemini_client.generate_response(prompt)
        
        # 속마음 생성
        inner_thought_obj = None
        try:
            inner_thought_obj = await generate_inner_thought(
                character=character,
                character_dialogue=response_text,
                user_message=user_message,
                relationship_data=relationship_data,
                location=location,
                scene_context=scene_context
            )
        except Exception as e:
            print(f"⚠️ 속마음 생성 오류 ({character.name}): {str(e)}")
        
        # inner_thought 객체를 dict로 변환
        inner_thought_dict = None
        if inner_thought_obj:
            inner_thought_dict = {
                "thought": inner_thought_obj.thought,
                "surface_emotion": inner_thought_obj.surface_emotion,
                "inner_emotion": inner_thought_obj.inner_emotion,
                "emotion_gap": inner_thought_obj.emotion_gap,
                "user_evaluation": inner_thought_obj.user_evaluation,
                "attitude_toward_user": inner_thought_obj.attitude_toward_user,
                "intention": inner_thought_obj.intention
            }
        
        return MainResponse(
            character_id=character.id,
            character_name=character.name,
            message=response_text,
            action="*끼어들며*",
            inner_thought=inner_thought_dict
        )
    except Exception as e:
        print(f"⚠️ 끼어들기 응답 생성 오류 ({character.name}): {str(e)}")
        return None


# ═══════════════════════════════════════════════════════════════
# 캐릭터 간 티키타카 (Mention Detection)
# ═══════════════════════════════════════════════════════════════

def detect_mentioned_characters_in_response(
    response_text: str,
    characters: List[CharacterPersona],
    exclude_character_id: str = None
) -> List[CharacterPersona]:
    """
    응답 텍스트에서 언급된 다른 캐릭터 감지
    
    Args:
        response_text: 캐릭터의 응답 텍스트
        characters: 전체 캐릭터 목록
        exclude_character_id: 제외할 캐릭터 ID (응답한 캐릭터)
    
    Returns:
        언급된 캐릭터 목록
    """
    mentioned = []
    
    for char in characters:
        if exclude_character_id and char.id == exclude_character_id:
            continue
        
        # 정확한 이름 매칭
        if char.name in response_text:
            mentioned.append(char)
            continue
        
        # 이름의 마지막 2글자 (예: "황인하" → "인하")
        if len(char.name) >= 2:
            short_name = char.name[-2:]
            if short_name in response_text:
                mentioned.append(char)
                continue
        
        # 애칭 패턴 (예: "인하야", "인하씨", "인하아")
        if len(char.name) >= 2:
            short_name = char.name[-2:]
            patterns = [
                f"{short_name}야",
                f"{short_name}씨",
                f"{short_name}아",
                f"{short_name}",
            ]
            for pattern in patterns:
                if pattern in response_text:
                    mentioned.append(char)
                    break
    
    return mentioned


async def generate_tikitaka_response(
    mentioned_character: CharacterPersona,
    mentioning_character: CharacterPersona,
    mentioning_message: str,
    user_message: str,
    scene_context: Optional[SceneContext],
    characters: List[CharacterPersona],
    location: str,
    relationship_data,
    user_id: str,
    recent_story_summaries: List[Dict] = None
) -> Optional[MainResponse]:
    """캐릭터 간 티키타카 응답 생성"""
    
    # 스토리 컨텍스트 추가
    story_context = ""
    if recent_story_summaries:
        from core.story_analyzer import build_story_context_for_prompt
        story_context = build_story_context_for_prompt(recent_story_summaries)
    
    prompt = f"""
당신은 '{mentioned_character.name}'입니다.

[캐릭터 정보]
{mentioned_character.personality[:500]}

{story_context}

[현재 상황]
장소: {location}
유저가 말했습니다: "{user_message}"

다른 캐릭터 '{mentioning_character.name}'이 당신의 이름을 부르며 말했습니다:
"{mentioning_message}"

[⚠️ 중요 지시사항]
1. **스토리 컨텍스트 활용**: 위의 "[📖 최근 스토리 흐름]"을 참고하여 이전 대화의 맥락을 활용하세요.
2. **일관성 유지**: 이전 대화에서 일어난 사건들을 기억하고 일관성 있게 응답하세요.

[요청]
당신은 '{mentioning_character.name}'이 당신을 직접 부른 것에 반응해야 합니다.
- 짧고 간결하게 응답하세요 (2-3문장)
- '{mentioning_character.name}'에게 직접 말을 걸되, 유저도 인지하세요
- 캐릭터의 말투와 성격을 100% 유지하세요
- 자연스러운 티키타카처럼 반응하세요
- 이전 대화의 맥락을 활용하여 일관성 있는 응답을 하세요

[응답 형식]
대사만 작성하세요. 행동 묘사는 *별표* 안에.
"""
    
    try:
        response_text = gemini_client.generate_response(prompt)
        
        # 속마음 생성
        inner_thought_obj = None
        try:
            inner_thought_obj = await generate_inner_thought(
                character=mentioned_character,
                character_dialogue=response_text,
                user_message=user_message,
                relationship_data=relationship_data,
                location=location,
                scene_context=scene_context
            )
        except Exception as e:
            print(f"⚠️ 속마음 생성 오류 ({mentioned_character.name}): {str(e)}")
        
        # inner_thought 객체를 dict로 변환
        inner_thought_dict = None
        if inner_thought_obj:
            inner_thought_dict = {
                "thought": inner_thought_obj.thought,
                "surface_emotion": inner_thought_obj.surface_emotion,
                "inner_emotion": inner_thought_obj.inner_emotion,
                "emotion_gap": inner_thought_obj.emotion_gap,
                "user_evaluation": inner_thought_obj.user_evaluation,
                "attitude_toward_user": inner_thought_obj.attitude_toward_user,
                "intention": inner_thought_obj.intention
            }
        
        return MainResponse(
            character_id=mentioned_character.id,
            character_name=mentioned_character.name,
            message=response_text,
            action=f"*{mentioning_character.name}에게 응답하며*",
            inner_thought=inner_thought_dict
        )
    except Exception as e:
        print(f"⚠️ 티키타카 응답 생성 오류 ({mentioned_character.name}): {str(e)}")
        return None


# ═══════════════════════════════════════════════════════════════
# 씬 리액션 생성 (메인 함수)
# ═══════════════════════════════════════════════════════════════

async def generate_scene_reaction(
    user_message: str,
    characters: List[CharacterPersona],
    scene_context: Optional[SceneContext],
    location: str,
    conversation_history: List[Dict],
    user_id: str,
    db: Session,
    recent_story_summaries: List[Dict] = None
) -> SceneReactionResult:
    """
    씬 리액션 생성
    
    Returns:
        SceneReactionResult: 메인 응답, 서브 리액션, 무반응 캐릭터
    """
    
    # 1. 반응 범위 분석
    reaction_scope = analyze_reaction_scope(user_message)
    print(f"[Scene Reaction] 반응 범위: {reaction_scope} (메시지: '{user_message}')")
    
    # 2. 직접 호명된 캐릭터 확인
    mentioned_characters = []
    for char in characters:
        if is_directly_mentioned(char, user_message):
            mentioned_characters.append(char.id)
            print(f"[Scene Reaction] 직접 호명: {char.name}")
    
    # 3. 캐릭터별 반응 타입 결정
    reaction_types = {}  # {character_id: "main" | "reaction" | "ignore"}
    
    for char in characters:
        directly_mentioned = char.id in mentioned_characters
        reaction_type = determine_reaction_type(
            character=char,
            character_id=char.id,
            scene_context=scene_context,
            user_message=user_message,
            reaction_scope=reaction_scope,
            directly_mentioned=directly_mentioned
        )
        reaction_types[char.id] = reaction_type
        print(f"[Scene Reaction] {char.name}: {reaction_type}")
    
    # 4. 메인 응답자 결정 (제한 없음)
    main_character_ids = [cid for cid, rtype in reaction_types.items() if rtype == "main"]
    
    # 직접 호명된 캐릭터 우선
    if mentioned_characters:
        main_character_ids = mentioned_characters  # 제한 없음
    elif not main_character_ids:
        # 메인 응답자가 없으면 이전 턴의 마지막 화자 선택
        if scene_context and scene_context.last_speaker_id:
            # 이전 마지막 화자가 있으면 그 캐릭터 선택
            main_character_ids = [scene_context.last_speaker_id]
        else:
            # 없으면 첫 번째 캐릭터 선택
            main_character_ids = [characters[0].id]
    
    # 제한 없음 - 모든 메인 응답자가 참여 가능
    
    print(f"[Scene Reaction] 메인 응답자: {main_character_ids}")
    
    # 5. 메인 응답 생성
    main_responses = []
    for char_id in main_character_ids:
        char = next((c for c in characters if c.id == char_id), None)
        if char:
            print(f"[Main Response] {char.name} 응답 생성 시작...")
            rel_data = get_relationship_data(
                user_id=user_id,
                character_id=char.id,
                db=db,
                create_if_not_exists=True
            )
            
            try:
                main_resp = await generate_main_response(
                    character=char,
                    user_message=user_message,
                    scene_context=scene_context,
                    characters=characters,
                    location=location,
                    conversation_history=conversation_history,
                    relationship_data=rel_data,
                    user_id=user_id,
                    recent_story_summaries=recent_story_summaries or []
                )
                main_responses.append(main_resp)
                print(f"[Main Response] {char.name} 응답 생성 완료: {main_resp.message[:50]}...")
            except Exception as e:
                print(f"⚠️ {char.name} 응답 생성 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ 캐릭터 ID '{char_id}'를 찾을 수 없음")
    
    print(f"[Main Response] 총 {len(main_responses)}명의 메인 응답 생성 완료")
    
    # ════════════════════════════════════════════════════════════
    # 5.3. 캐릭터 간 티키타카 (Mention Detection)
    # ════════════════════════════════════════════════════════════
    # 메인 응답에서 다른 캐릭터 이름이 언급되었는지 확인
    tikitaka_responses = []
    responded_character_ids = set(main_character_ids)  # 이미 응답한 캐릭터
    
    for main_resp in main_responses:
        # 이 응답에서 언급된 다른 캐릭터 찾기
        mentioned_chars = detect_mentioned_characters_in_response(
            response_text=main_resp.message,
            characters=characters,
            exclude_character_id=main_resp.character_id
        )
        
        for mentioned_char in mentioned_chars:
            # 이미 응답한 캐릭터는 제외
            if mentioned_char.id in responded_character_ids:
                continue
            
            print(f"[Tiki-Taka] {main_resp.character_name} → {mentioned_char.name} 언급 감지")
            
            # 티키타카 응답 생성
            rel_data = get_relationship_data(
                user_id=user_id,
                character_id=mentioned_char.id,
                db=db,
                create_if_not_exists=True
            )
            
            # 언급한 캐릭터 찾기
            mentioning_char = next((c for c in characters if c.id == main_resp.character_id), None)
            if not mentioning_char:
                continue
            
            tikitaka_resp = await generate_tikitaka_response(
                mentioned_character=mentioned_char,
                mentioning_character=mentioning_char,
                mentioning_message=main_resp.message,
                user_message=user_message,
                scene_context=scene_context,
                characters=characters,
                location=location,
                relationship_data=rel_data,
                user_id=user_id,
                recent_story_summaries=recent_story_summaries or []
            )
            
            if tikitaka_resp:
                tikitaka_responses.append(tikitaka_resp)
                responded_character_ids.add(mentioned_char.id)
                main_character_ids.append(mentioned_char.id)
                print(f"[Tiki-Taka] {mentioned_char.name} 응답 생성 완료")
    
    # 티키타카 응답을 메인 응답에 추가
    main_responses.extend(tikitaka_responses)
    
    # ════════════════════════════════════════════════════════════
    # 5.5. 끼어들기(Intervention) - 30% 확률, 최대 3명
    # ════════════════════════════════════════════════════════════
    import random
    INTERVENTION_PROBABILITY = 0.3  # 30% 확률 (전체적으로)
    MAX_INTERVENTIONS = 3  # 최대 3명
    
    # ⚠️ 핵심 수정: 먼저 전체적으로 끼어들기 여부를 30% 확률로 결정
    should_intervene = random.random() < INTERVENTION_PROBABILITY
    
    print(f"[Intervention] 끼어들기 체크: {should_intervene} (확률: {INTERVENTION_PROBABILITY*100}%)")
    
    if should_intervene:
        # 끼어들기로 결정됨 → 최대 3명까지 선택
        intervention_count = 0
        intervened_ids = set(main_character_ids)  # 이미 메인 응답자인 캐릭터 제외
        
        # 끼어들 수 있는 캐릭터 목록 (메인 응답자 제외)
        available_chars = [c for c in characters if c.id not in intervened_ids]
        
        # 랜덤하게 섞어서 최대 3명 선택
        random.shuffle(available_chars)
        
        for char in available_chars:
            if intervention_count >= MAX_INTERVENTIONS:
                break
            
            print(f"[Intervention] {char.name} 끼어들기 선택됨 ({intervention_count + 1}/{MAX_INTERVENTIONS})")
            
            rel_data = get_relationship_data(
                user_id=user_id,
                character_id=char.id,
                db=db,
                create_if_not_exists=True
            )
            
            # 끼어들기용 프롬프트로 응답 생성
            intervention_resp = await generate_intervention_response(
                character=char,
                user_message=user_message,
                main_responses=main_responses,
                scene_context=scene_context,
                characters=characters,
                location=location,
                relationship_data=rel_data,
                recent_story_summaries=recent_story_summaries or []
            )
            
            if intervention_resp:
                main_responses.append(intervention_resp)
                intervened_ids.add(char.id)
                intervention_count += 1
                
                # 메인 응답자 목록에도 추가
                main_character_ids.append(char.id)
        
        print(f"[Intervention] 총 {intervention_count}명 끼어듦")
    else:
        print(f"[Intervention] 끼어들기 없음 (확률 미통과)")
    
    # 6. 서브 리액션 생성 (메인 응답자 + 끼어든 캐릭터 제외)
    sub_reactions = []
    for char in characters:
        if char.id not in main_character_ids:
            reaction_type = reaction_types.get(char.id, "reaction")
            if reaction_type == "reaction":
                rel_data = get_relationship_data(
                    user_id=user_id,
                    character_id=char.id,
                    db=db,
                    create_if_not_exists=True
                )
                
                sub_react = await generate_sub_reaction(
                    character=char,
                    character_id=char.id,
                    user_message=user_message,
                    main_responses=main_responses,
                    scene_context=scene_context,
                    relationship_data=rel_data,
                    location=location
                )
                sub_reactions.append(sub_react)
    
    # 7. 무반응 캐릭터 (속마음만)
    no_reaction = []
    for char in characters:
        if char.id not in main_character_ids:
            reaction_type = reaction_types.get(char.id, "reaction")
            if reaction_type == "ignore":
                rel_data = get_relationship_data(
                    user_id=user_id,
                    character_id=char.id,
                    db=db,
                    create_if_not_exists=True
                )
                
                # 속마음만 생성
                inner_thought_obj = None
                try:
                    inner_thought_obj = await generate_inner_thought(
                        character=char,
                        character_dialogue="",
                        user_message=user_message,
                        relationship_data=rel_data,
                        location=location,
                        scene_context=scene_context
                    )
                except Exception as e:
                    print(f"⚠️ 속마음 생성 오류 ({char.name}): {str(e)}")
                
                inner_thought_dict = None
                if inner_thought_obj:
                    inner_thought_dict = {
                        "thought": inner_thought_obj.thought,
                        "surface_emotion": inner_thought_obj.surface_emotion,
                        "inner_emotion": inner_thought_obj.inner_emotion,
                        "emotion_gap": inner_thought_obj.emotion_gap,
                        "user_evaluation": inner_thought_obj.user_evaluation,
                    }
                
                no_reaction.append({
                    "character_id": char.id,
                    "character_name": char.name,
                    "inner_thought": inner_thought_dict
                })
    
    return SceneReactionResult(
        main_responses=main_responses,
        sub_reactions=sub_reactions,
        no_reaction=no_reaction
    )
