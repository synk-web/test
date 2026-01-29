"""
Speaker Selector Logic
멀티 캐릭터 대화에서 누가 응답할지 결정하는 로직
"""
import random
from typing import List, Optional, Tuple, Dict
from models.character import CharacterPersona
from models.scene_context import SceneContext, CharacterAttention


class ConversationHistory:
    """대화 히스토리 관리"""
    def __init__(self):
        self.turns: List[dict] = []  # [{"speaker": "user"|character_id, "message": str, "character_name": str}]
        self.last_speaker: Optional[str] = None  # 마지막에 말한 캐릭터 ID
    
    def add_turn(self, speaker: str, message: str, character_name: str = None):
        """대화 턴 추가"""
        self.turns.append({
            "speaker": speaker,
            "message": message,
            "character_name": character_name
        })
        if speaker != "user":
            self.last_speaker = speaker
    
    def get_recent_turns(self, count: int = 3) -> List[dict]:
        """최근 대화 턴들 가져오기"""
        return self.turns[-count:] if len(self.turns) >= count else self.turns
    
    def get_turn_count(self) -> int:
        """총 턴 수"""
        return len(self.turns)


def detect_mention(message: str, characters: List[CharacterPersona]) -> Optional[CharacterPersona]:
    """
    메시지에서 캐릭터 이름 언급 감지
    
    Args:
        message: 유저 메시지 또는 NPC 응답
        characters: 장소의 캐릭터들
    
    Returns:
        언급된 캐릭터 또는 None
    """
    message_lower = message.lower()
    
    for char in characters:
        # 이름이 메시지에 포함되어 있는지 확인
        if char.name in message or char.name.lower() in message_lower:
            return char
    
    return None


def detect_mentioned_npc(
    message: str,
    characters: List[CharacterPersona],
    exclude_character_id: Optional[str] = None
) -> Optional[CharacterPersona]:
    """
    NPC 응답에서 다른 NPC 언급 감지 (연쇄 반응용)
    
    Args:
        message: NPC 응답 메시지
        characters: 장소의 모든 캐릭터들
        exclude_character_id: 제외할 캐릭터 ID (현재 화자)
    
    Returns:
        언급된 다른 NPC 또는 None
    """
    message_lower = message.lower()
    
    for char in characters:
        # 현재 화자는 제외
        if exclude_character_id and char.id == exclude_character_id:
            continue
        
        # 이름이 메시지에 포함되어 있는지 확인
        if char.name in message or char.name.lower() in message_lower:
            return char
    
    return None


# ═══════════════════════════════════════════════════════════════
# 대명사 목록
# ═══════════════════════════════════════════════════════════════

PRONOUNS_TO_LAST_SPEAKER = [
    # 2인칭 대명사 (직전 화자 지칭)
    "넌", "너", "니가", "네가", "당신", "니", "네",
    "너는", "당신은", "당신이"
]

PRONOUNS_TO_SELF = [
    # 1인칭 대명사 (유저 자신)
    "나", "난", "내가", "저", "제가"
]


def select_speaker(
    message: str,
    characters: List[CharacterPersona],
    history: ConversationHistory,
    intervention_probability: float = 0.2,
    scene_context: Optional[SceneContext] = None
) -> CharacterPersona:
    """
    Speaker Selector Logic (개선 버전)
    
    규칙:
    1. 지명(Mention): 이름을 부르면 그 캐릭터가 응답
    2. @ 멘션: @캐릭터명 형식
    3. 대명사: "넌", "너" 등 → 직전 화자에게 응답
    4. 문맥(Context): 이름이 없으면, 마지막에 말한 캐릭터가 대화 이어감
    5. 최근 대화 참여자 우선
    6. 유저 주시 중인 캐릭터 우선
    7. 랜덤 난입(Intervention): 3턴 이상 지속되면 다른 캐릭터가 끼어들 확률
    
    Args:
        message: 유저 메시지
        characters: 장소의 캐릭터들
        history: 대화 히스토리
        intervention_probability: 랜덤 난입 확률 (기본 0.2 = 20%)
        scene_context: 씬 컨텍스트 (있으면 사용)
    
    Returns:
        응답할 캐릭터
    """
    # 캐릭터를 딕셔너리로 변환 (빠른 조회)
    char_dict = {char.id: char for char in characters}
    char_name_dict = {char.name: char for char in characters}
    
    # ─────────────────────────────────────
    # 1. 직접 이름 멘션 체크
    # ─────────────────────────────────────
    mentioned = detect_mention(message, characters)
    if mentioned:
        return mentioned
    
    # ─────────────────────────────────────
    # 2. @ 멘션 체크
    # ─────────────────────────────────────
    for char in characters:
        if f"@{char.name}" in message:
            return char
    
    # ─────────────────────────────────────
    # 3. Scene Context가 있으면 사용
    # ─────────────────────────────────────
    if scene_context:
        # 3-1. 대명사 체크 → 직전 화자
        for pronoun in PRONOUNS_TO_LAST_SPEAKER:
            if pronoun in message:
                if scene_context.last_speaker_id and scene_context.last_speaker_id in char_dict:
                    return char_dict[scene_context.last_speaker_id]
        
        # 3-2. 최근 대화 참여자
        recent_speakers = scene_context.get_recent_speakers()
        if recent_speakers and scene_context.last_speaker_id in recent_speakers:
            if scene_context.last_speaker_id in char_dict:
                return char_dict[scene_context.last_speaker_id]
        
        # 3-3. 유저 주시 중인 캐릭터
        watching_user = scene_context.get_characters_watching_user()
        if watching_user:
            char_id = watching_user[0]
            if char_id in char_dict:
                return char_dict[char_id]
        
        # 3-4. 활성 캐릭터 중 랜덤
        active_chars = [
            char_dict[char_id] for char_id, state in scene_context.character_states.items()
            if char_id in char_dict and state.attention != CharacterAttention.NONE
        ]
        if active_chars:
            return random.choice(active_chars)
    
    # ─────────────────────────────────────
    # 4. 폴백: 기존 로직 (히스토리 기반)
    # ─────────────────────────────────────
    # 대명사 체크 + 히스토리에서 마지막 화자 찾기
    for pronoun in PRONOUNS_TO_LAST_SPEAKER:
        if pronoun in message:
            if history.last_speaker and history.last_speaker in char_dict:
                return char_dict[history.last_speaker]
    
    # 마지막 화자 유지
    if history.last_speaker and history.last_speaker in char_dict:
        char = char_dict[history.last_speaker]
        # 랜덤 난입 체크 (3턴 이상이고 확률에 걸리면)
        turn_count = history.get_turn_count()
        if turn_count >= 3 and random.random() < intervention_probability:
            # 다른 캐릭터 중 랜덤 선택
            other_chars = [c for c in characters if c.id != char.id]
            if other_chars:
                return random.choice(other_chars)
        return char
    
    # 5. 기본값: 첫 번째 캐릭터
    return characters[0] if characters else None


def select_speaker_v2(
    user_message: str,
    location_characters: List[Dict],
    scene_context: Optional[SceneContext] = None,
    conversation_history: List[Dict] = None
) -> Tuple[str, str, str]:
    """
    개선된 화자 선택 로직 (딕셔너리 기반)
    
    Args:
        user_message: 유저 메시지
        location_characters: 해당 장소의 캐릭터 목록 (딕셔너리 리스트)
        scene_context: 씬 컨텍스트 (있으면 사용)
        conversation_history: 대화 히스토리 (scene_context 없을 때 폴백)
    
    Returns:
        (character_id, character_name, selection_reason)
    """
    # ─────────────────────────────────────
    # 1. 직접 이름 멘션 체크 (강화됨)
    # ─────────────────────────────────────
    for char in location_characters:
        char_name = char["name"]
        
        # 정확한 이름 매칭
        if char_name in user_message:
            print(f"[Speaker Selector] 직접 호명 감지: '{char_name}'")
            return char["id"], char_name, f"direct_mention:{char_name}"
        
        # 애칭/별명 매칭 (인하야, 인하씨, 인하 등)
        if len(char_name) >= 2:
            name_base = char_name[-2:]  # 마지막 2글자
            
            name_variations = [
                name_base,                    # 인하
                name_base + "야",            # 인하야
                name_base + "씨",            # 인하씨
                name_base + "아",            # 인하아
                name_base + "한테",          # 인하한테
                name_base + "에게",          # 인하에게
                name_base + "보고",          # 인하보고
            ]
            
            for variation in name_variations:
                if variation in user_message:
                    print(f"[Speaker Selector] 애칭/별명 감지: '{variation}' → '{char_name}'")
                    return char["id"], char_name, f"name_variation:{variation}→{char_name}"
    
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
    # 1. 직접 이름 호명 (최우선!) - 강화됨
    # ─────────────────────────────────────
    for char in location_characters:
        char_name = char["name"]
        
        # 정확한 이름 매칭
        if char_name in user_message:
            print(f"[Speaker Selector] 직접 호명 감지: '{char_name}'")
            return char["id"], char_name, f"direct_mention:{char_name}"
        
        # 애칭/별명 매칭 (인하야, 인하씨, 인하 등)
        # 이름의 마지막 2글자 추출 (예: "황인하" → "인하")
        if len(char_name) >= 2:
            name_base = char_name[-2:]  # 마지막 2글자
            
            name_variations = [
                name_base,                    # 인하
                name_base + "야",            # 인하야
                name_base + "씨",            # 인하씨
                name_base + "아",            # 인하아 (받침 없을 때)
                name_base + "한테",          # 인하한테
                name_base + "에게",          # 인하에게
                name_base + "보고",          # 인하보고
            ]
            
            for variation in name_variations:
                if variation in user_message:
                    print(f"[Speaker Selector] 애칭/별명 감지: '{variation}' → '{char_name}'")
                    return char["id"], char_name, f"name_variation:{variation}→{char_name}"
    
    # ─────────────────────────────────────
    # 2. 대명사 체크 → 직전 화자
    # ─────────────────────────────────────
    for pronoun in PRONOUNS_TO_LAST_SPEAKER:
        if pronoun in user_message:
            if context.last_speaker_id:
                char = next(
                    (c for c in location_characters if c["id"] == context.last_speaker_id),
                    None
                )
                if char:
                    # 디버그 로그
                    print(f"[Speaker Selector] 대명사 '{pronoun}' 감지 → 직전 화자 '{char['name']}' 선택")
                    return char["id"], char["name"], f"pronoun:{pronoun}→{char['name']}"
                else:
                    print(f"[Speaker Selector] ⚠️ 경고: last_speaker_id '{context.last_speaker_id}'에 해당하는 캐릭터를 찾을 수 없음")
    
    # ─────────────────────────────────────
    # 3. 유저 집중 패턴 체크 ("~한테", "~에게", "~보고")
    # ─────────────────────────────────────
    for char in location_characters:
        if len(char["name"]) >= 2:
            name_base = char["name"][-2:]
            target_patterns = [
                name_base + "한테",   # 인하한테
                name_base + "에게",   # 인하에게
                name_base + "보고",   # 인하보고
            ]
            for pattern in target_patterns:
                if pattern in user_message:
                    print(f"[Speaker Selector] 유저 집중 패턴 감지: '{pattern}' → '{char['name']}'")
                    return char["id"], char["name"], f"target_pattern:{pattern}→{char['name']}"
    
    # ─────────────────────────────────────
    # 4. 유저 주시 중인 recent 캐릭터 (유저 집중 우선)
    # ─────────────────────────────────────
    # 유저를 주시하고 있는 캐릭터 중 최근 대화 참여자 우선
    for char_id, state in context.character_states.items():
        if state.attention == CharacterAttention.USER and state.recent:
            char = next(
                (c for c in location_characters if c["id"] == char_id),
                None
            )
            if char:
                print(f"[Speaker Selector] 유저 집중 recent 캐릭터: '{char['name']}'")
                return char["id"], char["name"], f"user_focused_recent:{char['name']}"
    
    # ─────────────────────────────────────
    # 5. 최근 대화 참여자 (recent 태그)
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
    # 6. 유저 주시 중인 캐릭터
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
        char = random.choice(active_chars)
        return char["id"], char["name"], f"random_active:{char['name']}"
    
    # 최후의 수단: 전체 랜덤
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
    char = random.choice(location_characters)
    return char["id"], char["name"], f"random:{char['name']}"


def build_conversation_context(
    history: ConversationHistory,
    characters: List[CharacterPersona],
    max_turns: int = 5
) -> str:
    """
    대화 컨텍스트 프롬프트 생성
    
    Args:
        history: 대화 히스토리
        characters: 장소의 캐릭터들
        max_turns: 포함할 최대 턴 수
    
    Returns:
        컨텍스트 문자열
    """
    recent_turns = history.get_recent_turns(max_turns)
    
    if not recent_turns:
        return ""
    
    context_lines = ["[최근 대화]"]
    
    for turn in recent_turns:
        if turn["speaker"] == "user":
            context_lines.append(f"유저: {turn['message']}")
        else:
            char_name = turn.get("character_name", "캐릭터")
            context_lines.append(f"{char_name}: {turn['message']}")
    
    return "\n".join(context_lines)


# build_multi_character_context는 prompt_builder_v2.py로 이동 (중복 제거)
# 필요시 import: from core.prompt_builder_v2 import build_multi_character_context
