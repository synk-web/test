"""
캐릭터 속마음 모델
SYNK MVP - 캐릭터의 내면 생각 표시
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class InnerThought(BaseModel):
    """
    캐릭터 속마음
    
    캐릭터가 대사 외에 내면으로 생각하는 것을 표현합니다.
    유저가 캐릭터의 진짜 감정과 의도를 파악할 수 있습니다.
    """
    
    character_id: str
    character_name: str
    turn_id: str
    
    # ═══════════════════════════════════════
    # 속마음 내용
    # ═══════════════════════════════════════
    thought: str
    # 예: "뭐야, 이놈? 처음 보는 얼굴인데 눈빛이 예사롭지 않네."
    
    # ═══════════════════════════════════════
    # 감정 분석
    # ═══════════════════════════════════════
    surface_emotion: str           # 겉으로 보이는 감정 ("허세", "냉정", "무관심")
    inner_emotion: str             # 실제 감정 ("긴장", "호기심", "두려움")
    emotion_gap: bool = False      # 겉과 속이 다른지
    
    # ═══════════════════════════════════════
    # 유저 평가
    # ═══════════════════════════════════════
    user_evaluation: Optional[str] = None
    # 예: "만만해 보이지만 경계 필요"
    
    attitude_toward_user: Optional[str] = None
    # 예: "경계", "관심", "무시", "호감"
    
    # ═══════════════════════════════════════
    # 의도
    # ═══════════════════════════════════════
    intention: Optional[str] = None
    # 예: "기선제압하려 함", "떠보는 중", "무시하려 함"
    
    next_plan: Optional[str] = None
    # 예: "더 압박할 예정", "일단 관망", "도움을 줄까 고민"
    
    # ═══════════════════════════════════════
    # 메타데이터
    # ═══════════════════════════════════════
    timestamp: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════
# 속마음 생성 프롬프트
# ═══════════════════════════════════════════════════════════════

INNER_THOUGHT_PROMPT = """
[캐릭터 정보]
이름: {character_name}
성격: {character_personality}
유저와의 관계: {relationship_status}

[상황]
장소: {location}
{scene_context}

[캐릭터가 방금 한 말]
"{character_dialogue}"

[유저의 이전 말/행동]
{user_context}

[생성 요청]
{character_name}의 속마음을 작성하세요.
- 겉으로 한 말과 다를 수 있는 진짜 생각
- 유저에 대한 솔직한 평가
- 앞으로 어떻게 할지 의도

[중요]
- 캐릭터의 성격에 맞는 사고방식으로
- 1~2문장의 짧은 독백 형식
- 솔직하고 날것의 생각

[JSON 형식으로 응답]
{{
  "thought": "속마음 독백 (1~2문장)",
  "surface_emotion": "겉으로 보이는 감정",
  "inner_emotion": "실제 속 감정",
  "emotion_gap": true/false,
  "user_evaluation": "유저에 대한 평가",
  "attitude_toward_user": "유저를 대하는 태도",
  "intention": "현재 의도"
}}
"""


# ═══════════════════════════════════════════════════════════════
# 감정 매핑 (겉 vs 속)
# ═══════════════════════════════════════════════════════════════

EMOTION_PAIRS = {
    # (겉 감정, 속 감정) 예시
    "허세형": {
        "surface": ["당당함", "깔봄", "무시"],
        "inner": ["긴장", "불안", "열등감"]
    },
    "츤데레형": {
        "surface": ["짜증", "무관심", "냉정"],
        "inner": ["관심", "호감", "걱정"]
    },
    "쿨형": {
        "surface": ["무표정", "냉정", "귀찮음"],
        "inner": ["호기심", "재미있음", "놀람"]
    },
    "공격형": {
        "surface": ["분노", "적대감", "경멸"],
        "inner": ["두려움", "위기감", "질투"]
    }
}


def get_emotion_gap_description(surface: str, inner: str) -> str:
    """겉과 속 감정 차이 설명 생성"""
    if surface == inner:
        return "솔직한 상태"
    
    return f"겉으로는 '{surface}'이지만, 속으로는 '{inner}'"
