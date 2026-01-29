"""
멀티 캐릭터 채팅 API
씬 리액션 시스템: 여러 캐릭터가 동시에/순차적으로 반응
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.character_db import get_db, get_characters_by_location, get_location
from db.database import get_relationship_data, save_story_summary, get_recent_story_summaries
from core.speaker_selector import ConversationHistory, build_conversation_context
from core.scene_manager import scene_manager
from core.data_collector import process_turn
from core.user_profile_extractor import update_user_profile_from_message
from core.scene_reaction import generate_scene_reaction, SceneReactionResult
from core.story_analyzer import generate_story_summary, build_story_context_for_prompt
import asyncio
from models.character import CharacterPersona
from models.scene_context import CharacterAttention

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 세션별 대화 히스토리 저장
conversation_histories: Dict[str, ConversationHistory] = {}


class MultiChatRequest(BaseModel):
    """멀티 캐릭터 채팅 요청"""
    user_id: str
    location_id: str
    message: str
    session_id: Optional[str] = None


class MultiChatResponse(BaseModel):
    """멀티 캐릭터 채팅 응답 (씬 리액션 시스템)"""
    turn_id: str
    session_id: str
    location: str
    all_characters: List[dict]
    conversation_turn: int
    
    # 씬 리액션 시스템
    main_responses: List[dict]  # 메인 응답자들 (1~2명)
    sub_reactions: List[dict]  # 서브 리액션 (나머지)
    no_reaction: List[dict]  # 무반응 캐릭터 (속마음만)
    
    # 하위 호환성
    character_id: Optional[str] = None
    character_name: Optional[str] = None
    character_response: Optional[str] = None
    
    scene_context: Optional[dict] = None


@router.post("/location/{location_id}", response_model=MultiChatResponse)
async def chat_in_location(
    location_id: str,
    request: MultiChatRequest,
    db: Session = Depends(get_db)
):
    """
    특정 장소에서 멀티 캐릭터 대화 (씬 리액션 시스템)
    
    여러 캐릭터가 동시에/순차적으로 반응:
    - 메인 응답: 1~2명 (긴 대사)
    - 서브 리액션: 나머지 (짧은 반응)
    - 무반응: 관심 없는 캐릭터 (속마음만)
    """
    # 1. 장소 확인
    location = get_location(location_id, db)
    if not location:
        raise HTTPException(
            status_code=404,
            detail=f"장소 '{location_id}'를 찾을 수 없습니다."
        )
    
    # 2. 장소의 캐릭터들 조회
    characters = get_characters_by_location(location_id, db)
    if not characters:
        raise HTTPException(
            status_code=404,
            detail=f"장소 '{location_id}'에 캐릭터가 없습니다."
        )
    
    # 3. 세션 ID 생성 또는 사용
    session_id = request.session_id or f"{request.user_id}_{location_id}_{uuid.uuid4().hex[:8]}"
    
    # 4. Scene Context 조회 또는 생성
    characters_dict = [{"id": c.id, "name": c.name} for c in characters]
    scene_context = scene_manager.get_or_create_context(
        session_id=session_id,
        location=location.name,
        characters=characters_dict
    )
    
    # 5. 대화 히스토리 가져오기 또는 생성
    if session_id not in conversation_histories:
        conversation_histories[session_id] = ConversationHistory()
    history = conversation_histories[session_id]
    
    # 6. 유저 메시지 히스토리에 추가
    history.add_turn("user", request.message)
    
    # 7. 유저 프로필 자동 업데이트
    try:
        await update_user_profile_from_message(
            user_id=request.user_id,
            user_message=request.message,
            context={
                "location": location.name,
                "characters": [c.name for c in characters]
            },
            db=db
        )
    except Exception as e:
        print(f"⚠️ 유저 프로필 업데이트 오류: {str(e)}")
    
    # 8. 씬 리액션 생성 (핵심 로직)
    turn_id = str(uuid.uuid4())
    
    # ⚠️ 중요: 새 턴 시작 시 모든 캐릭터의 recent 플래그 리셋
    scene_context.reset_recent_flags()
    
    # 최근 스토리 요약 조회 (프롬프트 컨텍스트용)
    recent_story_summaries = get_recent_story_summaries(session_id, limit=5, db=db)
    
    scene_reaction = await generate_scene_reaction(
        user_message=request.message,
        characters=characters,
        scene_context=scene_context,
        location=location.name,
        conversation_history=history.get_recent_turns(5),
        user_id=request.user_id,
        db=db,
        recent_story_summaries=recent_story_summaries  # 스토리 컨텍스트 추가
    )
    
    # 9. Scene Context 업데이트 (모든 반응 캐릭터)
    # 9-1. 메인 응답자들 업데이트
    last_main_responder = None  # 마지막 메인 응답자 추적
    for main_resp in scene_reaction.main_responses:
        char = next((c for c in characters if c.id == main_resp.character_id), None)
        if char:
            rel_data = get_relationship_data(
                user_id=request.user_id,
                character_id=char.id,
                db=db,
                create_if_not_exists=True
            )
            
            scene_manager.process_character_response(
                session_id=session_id,
                character_id=main_resp.character_id,
                character_name=main_resp.character_name,
                response=main_resp.message,
                target="user",
                target_name="유저",
                inner_thought=main_resp.inner_thought,
                mood=rel_data.emotional_stats.joy_peaks > rel_data.emotional_stats.anger_peaks and "happy" or "neutral"
            )
            
            # 히스토리에 추가
            history.add_turn(
                speaker=main_resp.character_id,
                message=main_resp.message,
                character_name=main_resp.character_name
            )
            
            # 마지막 메인 응답자 추적
            last_main_responder = main_resp
    
    # 9-1.5. 스토리 요약 AI 생성 및 DB 저장
    print(f"[Story Summary] 시작 - 메인 응답자 수: {len(scene_reaction.main_responses)}")
    if scene_reaction.main_responses:
        try:
            # 캐릭터 응답 데이터 준비 (행동, 대사, 속마음 포함)
            character_responses_data = []
            for r in scene_reaction.main_responses:
                # 속마음 정보 추출
                inner_thought_dict = r.inner_thought if r.inner_thought else None
                inner_thought_text = None
                if inner_thought_dict:
                    if isinstance(inner_thought_dict, dict):
                        inner_thought_text = inner_thought_dict.get('thought', '')
                    else:
                        inner_thought_text = str(inner_thought_dict)
                
                character_responses_data.append({
                    "character_id": r.character_id,
                    "character_name": r.character_name,
                    "message": r.message,  # 전체 메시지 (요약은 AI가 수행)
                    "action": r.action or "",
                    "inner_thought": inner_thought_text
                })
            
            # 캐릭터 상태 데이터 준비 (모든 캐릭터의 상태와 속마음)
            character_states_data = {}
            if scene_context:
                for char_id, state in scene_context.character_states.items():
                    # 속마음 정보 추출
                    inner_thought_str = getattr(state, 'inner_thought', None)
                    if inner_thought_str:
                        if isinstance(inner_thought_str, dict):
                            inner_thought_str = inner_thought_str.get('thought', '')
                        else:
                            inner_thought_str = str(inner_thought_str)
                    
                    character_states_data[char_id] = {
                        "character_name": state.character_name,
                        "recent": state.recent,
                        "attention": state.attention.value if hasattr(state.attention, 'value') else str(state.attention),
                        "current_mood": getattr(state, 'current_mood', 'neutral'),
                        "inner_thought": inner_thought_str
                    }
            
            # 최근 스토리 요약 조회 (컨텍스트용)
            recent_summaries = get_recent_story_summaries(session_id, limit=10, db=db)
            
            # AI로 스토리 요약 생성 (타임아웃 5초)
            try:
                ai_summary, ai_analysis = await asyncio.wait_for(
                    generate_story_summary(
                        user_message=request.message,
                        character_responses=character_responses_data,
                        character_states=character_states_data,
                        recent_summaries=recent_summaries
                    ),
                    timeout=5.0
                )
                print(f"[Story Summary] AI 분석 완료: {ai_summary[:50]}...")
            except asyncio.TimeoutError:
                print("⚠️ 스토리 요약 생성 타임아웃 - 기본 요약 사용")
                # 타임아웃 시 행동 중심 기본 요약 생성
                main_resp = scene_reaction.main_responses[0] if scene_reaction.main_responses else None
                if main_resp:
                    action = main_resp.action or ""
                    # 행동 중심 요약 생성
                    if action:
                        ai_summary = f"유저가 '{request.message[:40]}...'라고 말했고, {main_resp.character_name}이 {action} 반응했다."
                    else:
                        ai_summary = f"유저가 '{request.message[:40]}...'라고 말했고, {main_resp.character_name}이 응답했다."
                    ai_analysis = f"{main_resp.character_name}이 유저의 발언에 반응하며 상황이 전개되었다."
                else:
                    ai_summary = f"유저가 '{request.message[:40]}...'라고 말했다."
                    ai_analysis = "대화가 진행되었다."
            except Exception as ai_error:
                print(f"⚠️ 스토리 요약 AI 생성 오류: {ai_error}")
                import traceback
                traceback.print_exc()
                # 에러 시 행동 중심 기본 요약 생성
                main_resp = scene_reaction.main_responses[0] if scene_reaction.main_responses else None
                if main_resp:
                    action = main_resp.action or ""
                    if action:
                        ai_summary = f"유저가 '{request.message[:40]}...'라고 말했고, {main_resp.character_name}이 {action} 반응했다."
                    else:
                        ai_summary = f"유저가 '{request.message[:40]}...'라고 말했고, {main_resp.character_name}이 응답했다."
                    ai_analysis = f"{main_resp.character_name}이 유저의 발언에 반응하며 상황이 전개되었다."
                else:
                    ai_summary = f"유저가 '{request.message[:40]}...'라고 말했다."
                    ai_analysis = "대화가 진행되었다."
            
            # DB에 저장
            turn_number = scene_context.total_turns if scene_context else 1
            turn_id = str(uuid.uuid4())
            
            try:
                print(f"[Story Summary] DB 저장 시도 - 세션: {session_id}, 턴: {turn_number}")
                save_story_summary(
                    session_id=session_id,
                    user_id=request.user_id,
                    location=location.name,
                    turn_number=turn_number,
                    turn_id=turn_id,
                    user_message=request.message,
                    character_responses=character_responses_data,
                    character_states=character_states_data,
                    ai_summary=ai_summary,
                    ai_analysis=ai_analysis,
                    db=db
                )
                print(f"[Story Summary] ✅ DB 저장 완료 (턴 {turn_number}): {ai_summary[:50]}...")
            except Exception as db_error:
                print(f"⚠️ 스토리 요약 DB 저장 오류: {db_error}")
                import traceback
                traceback.print_exc()
                # DB 저장 실패해도 계속 진행
            
            # Scene Context에도 추가 (기존 호환성) - 대사 포함하여 추가
            def clean_story_summary(text):
                """형식만 정리, 대사 내용은 유지"""
                import re
                if not text:
                    return text
                # 연속 공백만 정리 (대사는 유지)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
            
            cleaned_summary = clean_story_summary(ai_summary)
            if not cleaned_summary or len(cleaned_summary) < 5:
                cleaned_summary = ai_summary  # 정리 실패 시 원본 사용
            
            scene_manager.add_story_point(
                session_id=session_id,
                point=cleaned_summary
            )
            
        except Exception as e:
            print(f"⚠️ 스토리 요약 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            # 에러가 발생해도 대화는 계속 진행
    else:
        print(f"[Story Summary] ⚠️ 메인 응답자가 없어 스토리 요약 생성 건너뜀")
    
    # 9-2. 서브 리액션 캐릭터들도 속마음 업데이트 (recent=False, attention=OBSERVING)
    # 단, 이미 메인 응답자로 처리된 캐릭터는 건드리지 않음
    main_character_ids = {r.character_id for r in scene_reaction.main_responses}
    for sub_react in scene_reaction.sub_reactions:
        if sub_react.inner_thought and sub_react.character_id not in main_character_ids:
            # 서브 리액션은 response=""로 전달하여 recent=False, attention 유지
            scene_manager.process_character_response(
                session_id=session_id,
                character_id=sub_react.character_id,
                character_name=sub_react.character_name,
                response="",  # 빈 응답 = 서브 리액션
                target="user",
                target_name="유저",
                inner_thought=sub_react.inner_thought,
                mood=None
            )
            # 서브 리액션은 관찰 중 상태로 명시적 설정
            context = scene_manager.get_context(session_id)
            if context and sub_react.character_id in context.character_states:
                state = context.character_states[sub_react.character_id]
                state.attention = CharacterAttention.OBSERVING
                state.recent = False
    
    # 9-3. 무반응 캐릭터들도 속마음 업데이트 (recent=False, attention 유지)
    # 단, 이미 메인 응답자로 처리된 캐릭터는 건드리지 않음
    for no_react in scene_reaction.no_reaction:
        if no_react.get("inner_thought") and no_react["character_id"] not in main_character_ids:
            # 무반응은 response=""로 전달하여 recent=False, attention 유지
            scene_manager.process_character_response(
                session_id=session_id,
                character_id=no_react["character_id"],
                character_name=no_react["character_name"],
                response="",  # 빈 응답 = 무반응
                target="user",
                target_name="유저",
                inner_thought=no_react["inner_thought"],
                mood=None
            )
    
    # 10. 데이터 수집 및 관계 데이터 업데이트 (메인 응답자들)
    for main_resp in scene_reaction.main_responses:
        turn_data = {
            "turn_id": str(uuid.uuid4()),
            "user_message": request.message,
            "character_response": main_resp.message,
            "timestamp": datetime.now(),
        }
        
        try:
            await process_turn(
                user_id=request.user_id,
                character_id=main_resp.character_id,
                turn_data=turn_data,
                emoji_reaction=None,
                db=db
            )
        except Exception as e:
            print(f"⚠️ 데이터 수집 오류 ({main_resp.character_name}): {str(e)}")
    
    # 11. 응답 데이터 구성
    all_characters_info = [
        {
            "id": c.id,
            "name": c.name,
            "location": location.name
        }
        for c in characters
    ]
    
    # 마지막 메인 응답자를 기준으로 current_focus 업데이트
    if last_main_responder:
        scene_context.current_focus = f"유저 ↔ {last_main_responder.character_name}"
    
    # 최근 10턴의 스토리 요약 조회 (DB에서)
    recent_story_summaries = get_recent_story_summaries(session_id, limit=10, db=db)
    story_arc_list = [s['ai_summary'] for s in recent_story_summaries] if recent_story_summaries else []
    
    # Scene Context 딕셔너리 변환
    scene_context_dict = None
    if scene_context:
        scene_context_dict = {
            "location": scene_context.location,
            "tension": getattr(scene_context, 'tension_level', 0),
            "current_focus": scene_context.current_focus,
            "last_speaker_name": last_main_responder.character_name if last_main_responder else scene_context.last_speaker_name,
            "character_states": {
                char_id: {
                    "character_name": state.character_name,
                    "current_mood": getattr(state, 'mood', getattr(state, 'current_mood', 'neutral')),
                    "attention": state.attention.value if state.attention and hasattr(state.attention, 'value') else (state.attention if state.attention else None),
                    "attention_target": getattr(state, 'attention_target', None),
                    "recent": state.recent,
                    "inner_thought": state.inner_thought
                }
                for char_id, state in scene_context.character_states.items()
            },
            "tension_level": getattr(scene_context, 'tension_level', 5),
            "last_speaker_name": last_main_responder.character_name if last_main_responder else scene_context.last_speaker_name,
            "main_speakers": [r.character_name for r in scene_reaction.main_responses],  # 메인 응답자들
            "recent_events": [
                {
                    "speaker_name": event.speaker_name,
                    "target_name": event.target_name,
                    "summary": event.summary
                }
                for event in scene_context.recent_events[-5:]
            ],
            "story_arc": story_arc_list  # 최근 10턴의 스토리 요약 (DB에서 가져옴)
        }
    
    # 하위 호환성: 첫 번째 메인 응답자
    first_main = scene_reaction.main_responses[0] if scene_reaction.main_responses else None
    
    return MultiChatResponse(
        turn_id=turn_id,
        session_id=session_id,
        location=location.name,
        all_characters=all_characters_info,
        conversation_turn=history.get_turn_count(),
        main_responses=[
            {
                "character_id": r.character_id,
                "character_name": r.character_name,
                "message": r.message,
                "action": r.action,
                "inner_thought": r.inner_thought
            }
            for r in scene_reaction.main_responses
        ],
        sub_reactions=[
            {
                "character_id": r.character_id,
                "character_name": r.character_name,
                "reaction": r.reaction,
                "inner_thought": r.inner_thought
            }
            for r in scene_reaction.sub_reactions
        ],
        no_reaction=scene_reaction.no_reaction,
        character_id=first_main.character_id if first_main else None,
        character_name=first_main.character_name if first_main else None,
        character_response=first_main.message if first_main else None,
        scene_context=scene_context_dict
    )


@router.get("/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """대화 히스토리 조회"""
    if session_id not in conversation_histories:
        return {"turns": []}
    
    history = conversation_histories[session_id]
    return {
        "turns": history.turns,
        "turn_count": history.get_turn_count()
    }
