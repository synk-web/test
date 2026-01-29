"""
유저 프로필 자동 추출
SYNK MVP - 대화에서 유저 정보 자동 추출
"""
from typing import Optional, Dict
from models.user_profile import UserProfile
from utils.gemini_client import gemini_client
import json
import re


EXTRACTION_PROMPT = """
[유저 메시지]
{user_message}

[대화 맥락]
{context}

[추출할 정보]
1. 닉네임/이름 언급 여부
2. 능력 설명 여부 (능력명, 설명, 등급)
3. 성격 특성 (도발적, 소심함, 유머러스, 자신감 등)
4. 중요한 행동 (싸움, 협력, 거절, 위협 등)
5. 새로운 사실 (좋아하는 것, 싫어하는 것, 과거 경험 등)

[JSON 형식으로 응답]
{{
  "nickname": "추출된 이름 또는 null",
  "ability": {{
    "name": "능력명",
    "description": "설명",
    "rank": "등급 (S/A/B/C/D)",
    "type": "능력 타입"
  }} 또는 null,
  "traits": ["특성1", "특성2"],
  "action": "주요 행동" 또는 null,
  "facts": ["새로운 사실1", "사실2"],
  "likes": ["좋아하는 것"],
  "dislikes": ["싫어하는 것"]
}}
"""


async def extract_user_info(
    user_message: str,
    context: Dict = None
) -> Dict:
    """
    유저 메시지에서 프로필 정보 자동 추출
    
    Args:
        user_message: 유저 메시지
        context: 대화 맥락 (선택)
    
    Returns:
        추출된 정보 딕셔너리
    """
    context_str = ""
    if context:
        context_str = f"장소: {context.get('location', '알 수 없음')}\n"
        context_str += f"캐릭터: {', '.join(context.get('characters', []))}"
    
    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        context=context_str
    )
    
    try:
        response_text = gemini_client.generate_response(prompt)
        
        # JSON 파싱
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError:
            # 파싱 실패 시 기본값
            extracted_data = {
                "nickname": None,
                "ability": None,
                "traits": [],
                "action": None,
                "facts": [],
                "likes": [],
                "dislikes": []
            }
        
        return extracted_data
    
    except Exception as e:
        import traceback
        print(f"⚠️ 유저 정보 추출 오류: {str(e)}")
        print(traceback.format_exc())
        return {
            "nickname": None,
            "ability": None,
            "traits": [],
            "action": None,
            "facts": [],
            "likes": [],
            "dislikes": []
        }


async def update_user_profile_from_message(
    user_id: str,
    user_message: str,
    context: Dict,
    db
) -> Optional[UserProfile]:
    """
    유저 메시지에서 정보 추출하여 프로필 업데이트
    
    Args:
        user_id: 유저 ID
        user_message: 유저 메시지
        context: 대화 맥락
        db: DB 세션
    
    Returns:
        업데이트된 UserProfile
    """
    from db.user_profile_db import get_user_profile, update_user_profile
    
    # 프로필 가져오기
    profile = get_user_profile(user_id, db)
    if not profile:
        from db.user_profile_db import create_user_profile
        profile = create_user_profile(user_id, db)
    
    # 정보 추출
    extracted = await extract_user_info(user_message, context)
    
    # 프로필 업데이트
    if extracted.get("nickname"):
        profile.nickname = extracted["nickname"]
    
    if extracted.get("ability"):
        ability = extracted["ability"]
        profile.ability_name = ability.get("name")
        profile.ability_description = ability.get("description")
        profile.ability_rank = ability.get("rank")
        profile.ability_type = ability.get("type")
    
    # 성격 특성 추가
    for trait in extracted.get("traits", []):
        profile.add_trait(trait)
    
    # 사실 추가
    for fact in extracted.get("facts", []):
        profile.add_fact(fact)
    
    # 좋아하는 것/싫어하는 것
    for like in extracted.get("likes", []):
        if like not in profile.likes:
            profile.likes.append(like)
    
    for dislike in extracted.get("dislikes", []):
        if dislike not in profile.dislikes:
            profile.dislikes.append(dislike)
    
    # 주요 행동 추가
    if extracted.get("action") and context.get("location"):
        profile.add_action(
            action=extracted["action"],
            location=context["location"],
            characters=context.get("characters", [])
        )
    
    # 프로필 저장
    updated_profile = update_user_profile(profile, db)
    
    return updated_profile
