"""
이모지 리액션 API
SYNK MVP - 유저가 캐릭터 대사에 이모지로 반응하는 시스템
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from db.character_db import get_db, get_character
from db.database import get_relationship_data
from core.data_collector import process_turn

router = APIRouter(prefix="/api/reaction", tags=["reaction"])


class ReactionRequest(BaseModel):
    """이모지 리액션 요청"""
    user_id: str
    character_id: str
    turn_id: str
    emoji: str  # ❤️, 💢, 🔥, ⭐
    user_message: Optional[str] = ""  # 유저 메시지 (컨텍스트용)
    character_response: Optional[str] = ""  # 캐릭터 응답 (컨텍스트용)


class ReactionResponse(BaseModel):
    """이모지 리액션 응답"""
    success: bool
    message: str
    relationship_data: Optional[dict] = None


@router.post("/", response_model=ReactionResponse)
async def add_reaction(
    request: ReactionRequest,
    db: Session = Depends(get_db)
):
    """
    이모지 리액션 추가
    
    이모지 종류:
    - ❤️ (심쿵): emotion="joy", intimacy +0.3, joy_peaks +1
    - 💢 (짜증): emotion="anger", anger_peaks +1, 트리거 후보 등록
    - 🔥 (열광): emotion="excitement", excitement_peaks +1
    - ⭐ (기억해!): core_memory 생성
    """
    # 이모지 유효성 검사
    valid_emojis = ["❤️", "💢", "🔥", "⭐"]
    if request.emoji not in valid_emojis:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 이모지입니다. 사용 가능: {', '.join(valid_emojis)}"
        )
    
    # 캐릭터 확인
    character = get_character(request.character_id, db)
    if not character:
        raise HTTPException(
            status_code=404,
            detail=f"캐릭터 '{request.character_id}'를 찾을 수 없습니다."
        )
    
    # 관계 데이터 가져오기 (없으면 생성)
    rel_data = get_relationship_data(
        user_id=request.user_id,
        character_id=request.character_id,
        db=db,
        create_if_not_exists=True
    )
    
    if not rel_data:
        raise HTTPException(
            status_code=500,
            detail="관계 데이터를 가져올 수 없습니다."
        )
    
    # 이모지에 따른 처리
    emoji_names = {
        "❤️": "심쿵",
        "💢": "짜증",
        "🔥": "열광",
        "⭐": "기억해!"
    }
    
    emoji_name = emoji_names.get(request.emoji, "반응")
    
    # 턴 데이터 구성
    turn_data = {
        "turn_id": request.turn_id,
        "user_message": request.user_message or "",
        "character_response": request.character_response or "",
        "timestamp": datetime.now(),
    }
    
    # 이모지 리액션 처리
    try:
        updated_rel_data = await process_turn(
            user_id=request.user_id,
            character_id=request.character_id,
            turn_data=turn_data,
            emoji_reaction=request.emoji,
            db=db
        )
        
        if not updated_rel_data:
            raise HTTPException(
                status_code=500,
                detail="데이터 처리 중 오류가 발생했습니다."
            )
        
        # 응답 메시지 생성
        messages = {
            "❤️": f"심쿵 반응이 기록되었습니다! {character.name}과(와)의 친밀도가 올라갔어요.",
            "💢": f"짜증 반응이 기록되었습니다. {character.name}의 말에서 트리거 키워드를 찾고 있어요.",
            "🔥": f"열광 반응이 기록되었습니다! {character.name}의 말이 정말 인상적이었나봐요.",
            "⭐": f"이 순간이 핵심 기억으로 저장되었습니다. {character.name}이(가) 이 대화를 기억할 거예요."
        }
        
        # 관계 데이터 요약
        relationship_summary = {
            "intimacy": updated_rel_data.intimacy,
            "dominance": updated_rel_data.dominance.score,
            "emotional_stats": {
                "joy_peaks": updated_rel_data.emotional_stats.joy_peaks,
                "anger_peaks": updated_rel_data.emotional_stats.anger_peaks,
                "excitement_peaks": updated_rel_data.emotional_stats.excitement_peaks,
                "sadness_peaks": updated_rel_data.emotional_stats.sadness_peaks,
                "fear_peaks": updated_rel_data.emotional_stats.fear_peaks,
            },
            "core_memories_count": len(updated_rel_data.core_memories),
            "trigger_keywords_count": len(updated_rel_data.trigger_keywords),
            "total_turns": updated_rel_data.total_turns
        }
        
        return ReactionResponse(
            success=True,
            message=messages.get(request.emoji, f"{emoji_name} 반응이 기록되었습니다."),
            relationship_data=relationship_summary
        )
    
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"⚠️ 이모지 리액션 처리 오류: {error_detail}")
        print(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"이모지 리액션 처리 중 오류가 발생했습니다: {error_detail}"
        )


@router.get("/relationship/{user_id}/{character_id}")
async def get_relationship_after_reaction(
    user_id: str,
    character_id: str,
    db: Session = Depends(get_db)
):
    """이모지 리액션 후 관계 데이터 조회"""
    rel_data = get_relationship_data(user_id, character_id, db)
    
    if not rel_data:
        raise HTTPException(
            status_code=404,
            detail="관계 데이터를 찾을 수 없습니다."
        )
    
    return {
        "success": True,
        "relationship_data": {
            "intimacy": rel_data.intimacy,
            "dominance": rel_data.dominance.score,
            "emotional_stats": {
                "joy_peaks": rel_data.emotional_stats.joy_peaks,
                "anger_peaks": rel_data.emotional_stats.anger_peaks,
                "excitement_peaks": rel_data.emotional_stats.excitement_peaks,
            },
            "core_memories_count": len(rel_data.core_memories),
            "trigger_keywords_count": len(rel_data.trigger_keywords),
        }
    }
