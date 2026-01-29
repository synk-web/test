"""
오프닝 시나리오 API
게임 시작 시 유저가 선택할 수 있는 오프닝 시나리오 처리
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from db.character_db import get_db, get_location, get_character

router = APIRouter(prefix="/api/opening", tags=["opening"])

# 오프닝 시나리오 데이터
OPENING_SCENARIOS = {
    "option_1": {
        "id": "option_1",
        "title": "현실 직시",
        "subtitle": "의무실",
        "description": "3일간 의식을 잃고 깨어난 당신. 담임 교수 심나은이 차갑게 말을 건넨다.",
        "location": "의무실",
        "npc_id": "npc_sim_naeun",
        "npc_name": "심나은",
        "opening_line": "…어, 일어났냐? 3일이나 퍼질러 자더군. 퇴원 수속 밟고 짐 싸서 '베타 동'으로 꺼져. 넌 오늘부터 빌런과니까.",
        "background_color": "#8B7355",  # 갈색 톤 (의무실)
        "icon": "🏥"
    },
    "option_2": {
        "id": "option_2",
        "title": "소꿉친구",
        "subtitle": "아카데미 정문",
        "description": "정문에서 기다리던 소꿉친구 이가은이 당신을 반갑게 맞이한다.",
        "location": "아카데미_정문",
        "npc_id": "npc_lee_gaeun",
        "npc_name": "이가은",
        "opening_line": "야!! 멍청아, 왜 이제 와! 내가 얼마나 기다렸는데! 너 빌런과 갔다며? 괜찮아, 누나가 지켜준다. 가자!",
        "background_color": "#4A90E2",  # 파란색 톤 (정문)
        "icon": "🚪"
    },
    "option_3": {
        "id": "option_3",
        "title": "신고식",
        "subtitle": "베타 동 로비",
        "description": "빌런과 기숙사 로비. 주창윤을 비롯한 5명의 학생들이 당신을 경계의 눈으로 바라본다.",
        "location": "베타_동_로비",
        "npc_id": "npc_joo_changyun",
        "npc_name": "주창윤",
        "opening_line": "하... 야. 문 닫아. 냄새 들어오잖아. ...뭐야 이 맹하게 생긴 놈은? 신입이냐?",
        "background_color": "#E74C3C",  # 빨간색 톤 (위험한 곳)
        "icon": "🔥"
    },
    "option_4": {
        "id": "option_4",
        "title": "공포",
        "subtitle": "지하 훈련장",
        "description": "어둡고 음침한 지하 훈련장. 최강의 전투광 신채린이 당신을 발견했다.",
        "location": "지하_훈련장",
        "npc_id": "npc_shin_chaerin",
        "npc_name": "신채린",
        "opening_line": "어라...? 여기 들어오면 안 되는데. ...길 잃었어? 아니면... 나랑 놀아주러 왔어?",
        "background_color": "#2C3E50",  # 어두운 회색 톤 (공포)
        "icon": "⚔️"
    }
}


class OpeningRequest(BaseModel):
    """오프닝 시나리오 선택 요청"""
    user_id: str
    scenario_id: str  # "option_1", "option_2", "option_3", "option_4"


class OpeningResponse(BaseModel):
    """오프닝 시나리오 응답"""
    status: str
    scenario_id: str
    location: str
    location_name: str
    npc_id: str
    npc_name: str
    opening_line: str
    session_id: str  # 채팅 세션 ID


@router.get("/scenarios")
async def get_opening_scenarios():
    """오프닝 시나리오 목록 조회"""
    return {
        "success": True,
        "scenarios": list(OPENING_SCENARIOS.values())
    }


@router.post("/start", response_model=OpeningResponse)
async def start_game(
    request: OpeningRequest,
    db: Session = Depends(get_db)
):
    """
    게임 시작 - 오프닝 시나리오 선택
    
    1. 선택한 시나리오의 장소로 이동
    2. 첫 대사를 대화 히스토리에 저장
    3. 채팅 세션 생성
    """
    # 1. 시나리오 확인
    scenario = OPENING_SCENARIOS.get(request.scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"시나리오 '{request.scenario_id}'를 찾을 수 없습니다."
        )
    
    # 2. 장소 확인
    location = get_location(scenario["location"], db)
    if not location:
        raise HTTPException(
            status_code=404,
            detail=f"장소 '{scenario['location']}'를 찾을 수 없습니다."
        )
    
    # 3. NPC 확인
    npc = get_character(scenario["npc_id"], db)
    if not npc:
        raise HTTPException(
            status_code=404,
            detail=f"캐릭터 '{scenario['npc_id']}'를 찾을 수 없습니다."
        )
    
    # 4. 세션 ID 생성 (user_id + location + timestamp)
    import uuid
    from datetime import datetime
    session_id = f"{request.user_id}_{scenario['location']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 5. 대화 히스토리에 첫 대사 추가 (chat_multi의 conversation_histories에)
    from api.chat_multi import conversation_histories
    from core.speaker_selector import ConversationHistory
    
    if session_id not in conversation_histories:
        conversation_histories[session_id] = ConversationHistory()
    
    history = conversation_histories[session_id]
    history.add_turn(
        speaker=scenario["npc_id"],
        message=scenario["opening_line"],
        character_name=scenario["npc_name"]
    )
    
    return OpeningResponse(
        status="success",
        scenario_id=request.scenario_id,
        location=scenario["location"],
        location_name=location.name,
        npc_id=scenario["npc_id"],
        npc_name=scenario["npc_name"],
        opening_line=scenario["opening_line"],
        session_id=session_id
    )
