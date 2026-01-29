"""
유저 프로필 데이터베이스
SYNK MVP - 유저(주인공) 프로필 저장/조회
"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from db.database import UserProfileTable, SessionLocal
from models.user_profile import UserProfile, CharacterImpression, UserAction


def get_user_profile(user_id: str, db: Session) -> Optional[UserProfile]:
    """유저 프로필 조회"""
    row = db.query(UserProfileTable).filter(UserProfileTable.user_id == user_id).first()
    
    if not row:
        return None
    
    # JSON 필드 파싱
    personality_traits = json.loads(row.personality_traits or "[]")
    character_impressions_data = json.loads(row.character_impressions or "{}")
    key_actions_data = json.loads(row.key_actions or "[]")
    mentioned_facts = json.loads(row.mentioned_facts or "[]")
    likes = json.loads(row.likes or "[]")
    dislikes = json.loads(row.dislikes or "[]")
    
    # CharacterImpression 변환
    character_impressions = {}
    for char_id, imp_data in character_impressions_data.items():
        character_impressions[char_id] = CharacterImpression(**imp_data)
    
    # UserAction 변환
    key_actions = []
    for action_data in key_actions_data:
        if "timestamp" in action_data and isinstance(action_data["timestamp"], str):
            action_data["timestamp"] = datetime.fromisoformat(action_data["timestamp"])
        key_actions.append(UserAction(**action_data))
    
    return UserProfile(
        user_id=row.user_id,
        nickname=row.nickname,
        gender=row.gender,
        ability_name=row.ability_name,
        ability_description=row.ability_description,
        ability_rank=row.ability_rank,
        ability_type=row.ability_type,
        personality_traits=personality_traits,
        speech_style=row.speech_style,
        character_impressions=character_impressions,
        key_actions=key_actions,
        mentioned_facts=mentioned_facts,
        likes=likes,
        dislikes=dislikes,
        total_turns=row.total_turns or 0,
        favorite_character=row.favorite_character,
        created_at=row.created_at,
        updated_at=row.updated_at
    )


def create_user_profile(user_id: str, db: Session) -> UserProfile:
    """유저 프로필 생성"""
    profile = UserProfile(user_id=user_id)
    return update_user_profile(profile, db)


def update_user_profile(profile: UserProfile, db: Session) -> UserProfile:
    """유저 프로필 업데이트"""
    row = db.query(UserProfileTable).filter(UserProfileTable.user_id == profile.user_id).first()
    
    if not row:
        # 새로 생성
        row = UserProfileTable(
            user_id=profile.user_id,
            nickname=profile.nickname,
            gender=profile.gender,
            ability_name=profile.ability_name,
            ability_description=profile.ability_description,
            ability_rank=profile.ability_rank,
            ability_type=profile.ability_type,
            personality_traits=json.dumps(profile.personality_traits, ensure_ascii=False),
            speech_style=profile.speech_style,
            character_impressions=json.dumps(
                {k: {
                    "status": v.status,
                    "impression": v.impression,
                    "key_events": v.key_events,
                    "last_updated": v.last_updated.isoformat() if isinstance(v.last_updated, datetime) else str(v.last_updated)
                } for k, v in profile.character_impressions.items()},
                ensure_ascii=False
            ),
            key_actions=json.dumps(
                [{
                    "action": a.action,
                    "location": a.location,
                    "involved_characters": a.involved_characters,
                    "timestamp": a.timestamp.isoformat() if isinstance(a.timestamp, datetime) else str(a.timestamp)
                } for a in profile.key_actions],
                ensure_ascii=False
            ),
            mentioned_facts=json.dumps(profile.mentioned_facts, ensure_ascii=False),
            likes=json.dumps(profile.likes, ensure_ascii=False),
            dislikes=json.dumps(profile.dislikes, ensure_ascii=False),
            total_turns=profile.total_turns,
            favorite_character=profile.favorite_character,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        db.add(row)
    else:
        # 업데이트
        row.nickname = profile.nickname
        row.gender = profile.gender
        row.ability_name = profile.ability_name
        row.ability_description = profile.ability_description
        row.ability_rank = profile.ability_rank
        row.ability_type = profile.ability_type
        row.personality_traits = json.dumps(profile.personality_traits, ensure_ascii=False)
        row.speech_style = profile.speech_style
        row.character_impressions = json.dumps(
            {k: {
                "status": v.status,
                "impression": v.impression,
                "key_events": v.key_events,
                "last_updated": v.last_updated.isoformat() if isinstance(v.last_updated, datetime) else str(v.last_updated)
            } for k, v in profile.character_impressions.items()},
            ensure_ascii=False
        )
        row.key_actions = json.dumps(
            [{
                "action": a.action,
                "location": a.location,
                "involved_characters": a.involved_characters,
                "timestamp": a.timestamp.isoformat() if isinstance(a.timestamp, datetime) else str(a.timestamp)
            } for a in profile.key_actions],
            ensure_ascii=False
        )
        row.mentioned_facts = json.dumps(profile.mentioned_facts, ensure_ascii=False)
        row.likes = json.dumps(profile.likes, ensure_ascii=False)
        row.dislikes = json.dumps(profile.dislikes, ensure_ascii=False)
        row.total_turns = profile.total_turns
        row.favorite_character = profile.favorite_character
        row.updated_at = datetime.now()
    
    db.commit()
    db.refresh(row)
    
    return get_user_profile(profile.user_id, db)
