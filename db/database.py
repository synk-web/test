"""
관계 데이터베이스
SYNK MVP - 유저와 캐릭터 간의 관계 데이터 저장/조회
"""
import json
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from models.relationship import RelationshipData, EmotionalStats, Dominance, CoreMemory, TriggerKeyword
from models.user_profile import UserProfile, CharacterImpression, UserAction

Base = declarative_base()


class RelationshipTable(Base):
    """관계 데이터 테이블"""
    __tablename__ = "relationships"
    
    # 기본 키
    user_id = Column(String, primary_key=True)
    character_id = Column(String, primary_key=True)
    
    # 친밀도
    intimacy = Column(Float, default=0.0)
    
    # Dominance (JSON)
    dominance_score = Column(Float, default=0.0)
    dominance_history = Column(Text)  # JSON array
    
    # 감정 통계 (JSON)
    emotional_stats = Column(Text)  # JSON object
    
    # 핵심 기억 (JSON)
    core_memories = Column(Text)  # JSON array
    
    # 트리거 키워드 (JSON)
    trigger_keywords = Column(Text)  # JSON array
    
    # 메타데이터
    total_turns = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserProfileTable(Base):
    """유저 프로필 테이블 (명세서 v2)"""
    __tablename__ = "user_profiles"
    
    user_id = Column(String, primary_key=True)
    
    # 기본 정보
    nickname = Column(String)
    gender = Column(String)
    
    # 능력 정보
    ability_name = Column(String)
    ability_description = Column(Text)
    ability_rank = Column(String)
    ability_type = Column(String)
    
    # 성격/특성
    personality_traits = Column(Text)  # JSON array
    speech_style = Column(Text)
    
    # 캐릭터별 인상 (JSON)
    character_impressions = Column(Text)  # JSON object
    
    # 행동 히스토리 (JSON)
    key_actions = Column(Text)  # JSON array
    mentioned_facts = Column(Text)  # JSON array
    
    # 선호도
    likes = Column(Text)  # JSON array
    dislikes = Column(Text)  # JSON array
    
    # 통계
    total_turns = Column(Integer, default=0)
    favorite_character = Column(String)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class StorySummaryTable(Base):
    """스토리 요약 테이블 - 대화 내용과 AI 분석 요약 저장"""
    __tablename__ = "story_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    
    # 턴 정보
    turn_number = Column(Integer, nullable=False)
    turn_id = Column(String, nullable=False)
    
    # 대화 내용
    user_message = Column(Text, nullable=False)
    character_responses = Column(Text)  # JSON array: [{"character_id": "...", "character_name": "...", "message": "..."}]
    character_states = Column(Text)  # JSON object: {character_id: {recent, attention, mood, inner_thought}}
    
    # AI 생성 요약
    ai_summary = Column(Text)  # AI가 생성한 스토리 요약
    ai_analysis = Column(Text)  # AI가 분석한 상황 묘사
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.now)


# DB 연결 (캐릭터 DB와 동일한 DB 사용)
from utils.config import get_database_url

DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """관계 데이터 DB 초기화 (user_profiles 테이블 포함)"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """DB 세션"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# 관계 데이터 CRUD
# ═══════════════════════════════════════════════════════════

def row_to_model(row: RelationshipTable) -> RelationshipData:
    """테이블 → 모델 변환"""
    # Dominance
    dominance = Dominance(
        score=row.dominance_score or 0.0,
        history=json.loads(row.dominance_history or "[]")
    )
    
    # EmotionalStats
    stats_data = json.loads(row.emotional_stats or "{}")
    emotional_stats = EmotionalStats(**stats_data)
    
    # CoreMemories
    try:
        memories_data = json.loads(row.core_memories or "[]")
    except:
        memories_data = []
    
    core_memories = []
    for m in memories_data:
        try:
            # datetime 문자열을 datetime 객체로 변환
            if "timestamp" in m:
                if isinstance(m["timestamp"], str):
                    try:
                        # ISO 형식 문자열 파싱
                        ts_str = m["timestamp"].replace("Z", "+00:00")
                        m["timestamp"] = datetime.fromisoformat(ts_str)
                    except Exception as e:
                        # 파싱 실패 시 현재 시간 사용
                        m["timestamp"] = datetime.now()
                elif not isinstance(m["timestamp"], datetime):
                    m["timestamp"] = datetime.now()
            else:
                m["timestamp"] = datetime.now()
            core_memories.append(CoreMemory(**m))
        except Exception as e:
            # 개별 메모리 파싱 실패 시 스킵
            print(f"⚠️ CoreMemory 파싱 오류: {e}")
            continue
    
    # TriggerKeywords
    try:
        triggers_data = json.loads(row.trigger_keywords or "[]")
    except:
        triggers_data = []
    
    trigger_keywords = []
    for t in triggers_data:
        try:
            # datetime 문자열을 datetime 객체로 변환
            if "first_occurrence" in t:
                if isinstance(t["first_occurrence"], str):
                    try:
                        # ISO 형식 문자열 파싱
                        ts_str = t["first_occurrence"].replace("Z", "+00:00")
                        t["first_occurrence"] = datetime.fromisoformat(ts_str)
                    except Exception as e:
                        # 파싱 실패 시 현재 시간 사용
                        t["first_occurrence"] = datetime.now()
                elif not isinstance(t["first_occurrence"], datetime):
                    t["first_occurrence"] = datetime.now()
            else:
                t["first_occurrence"] = datetime.now()
            trigger_keywords.append(TriggerKeyword(**t))
        except Exception as e:
            # 개별 트리거 파싱 실패 시 스킵
            print(f"⚠️ TriggerKeyword 파싱 오류: {e}")
            continue
    
    return RelationshipData(
        user_id=row.user_id,
        character_id=row.character_id,
        intimacy=row.intimacy or 0.0,
        dominance=dominance,
        emotional_stats=emotional_stats,
        core_memories=core_memories,
        trigger_keywords=trigger_keywords,
        total_turns=row.total_turns or 0,
        created_at=row.created_at,
        updated_at=row.updated_at
    )


def _serialize_datetime(obj):
    """datetime 객체를 ISO 형식 문자열로 변환"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def model_to_row(rel_data: RelationshipData, existing: RelationshipTable = None) -> RelationshipTable:
    """모델 → 테이블 변환"""
    row = existing or RelationshipTable()
    
    try:
        row.user_id = rel_data.user_id
        row.character_id = rel_data.character_id
        row.intimacy = rel_data.intimacy
        row.dominance_score = rel_data.dominance.score
        row.dominance_history = json.dumps(rel_data.dominance.history, ensure_ascii=False, default=str)
        
        # EmotionalStats - Pydantic v2 호환
        try:
            stats_dict = rel_data.emotional_stats.model_dump() if hasattr(rel_data.emotional_stats, 'model_dump') else rel_data.emotional_stats.dict()
        except:
            stats_dict = rel_data.emotional_stats.dict()
        row.emotional_stats = json.dumps(stats_dict, ensure_ascii=False, default=str)
        
        # CoreMemories - datetime 직렬화 처리
        memories_list = []
        for m in rel_data.core_memories:
            try:
                # Pydantic v2 호환
                if hasattr(m, 'model_dump'):
                    mem_dict = m.model_dump(mode='python')
                else:
                    mem_dict = m.dict()
            except:
                mem_dict = {
                    "summary": m.summary,
                    "memorable_quote": m.memorable_quote,
                    "timestamp": m.timestamp.isoformat() if isinstance(m.timestamp, datetime) else str(m.timestamp),
                    "trigger_keywords": m.trigger_keywords,
                    "emotion": m.emotion
                }
            # datetime을 ISO 형식 문자열로 변환
            if "timestamp" in mem_dict:
                if isinstance(mem_dict["timestamp"], datetime):
                    mem_dict["timestamp"] = mem_dict["timestamp"].isoformat()
            memories_list.append(mem_dict)
        row.core_memories = json.dumps(memories_list, ensure_ascii=False, default=_serialize_datetime)
        
        # TriggerKeywords - datetime 직렬화 처리
        triggers_list = []
        for t in rel_data.trigger_keywords:
            try:
                # Pydantic v2 호환
                if hasattr(t, 'model_dump'):
                    trigger_dict = t.model_dump(mode='python')
                else:
                    trigger_dict = t.dict()
            except:
                trigger_dict = {
                    "keyword": t.keyword,
                    "emotion": t.emotion,
                    "occurrence_count": t.occurrence_count,
                    "confidence": t.confidence,
                    "first_occurrence": t.first_occurrence.isoformat() if isinstance(t.first_occurrence, datetime) else str(t.first_occurrence)
                }
            # datetime을 ISO 형식 문자열로 변환
            if "first_occurrence" in trigger_dict:
                if isinstance(trigger_dict["first_occurrence"], datetime):
                    trigger_dict["first_occurrence"] = trigger_dict["first_occurrence"].isoformat()
            triggers_list.append(trigger_dict)
        row.trigger_keywords = json.dumps(triggers_list, ensure_ascii=False, default=_serialize_datetime)
        
        row.total_turns = rel_data.total_turns
        row.updated_at = datetime.now()
        
        if not existing:
            row.created_at = datetime.now()
        
        return row
    except Exception as e:
        import traceback
        print(f"⚠️ model_to_row 오류: {e}")
        print(traceback.format_exc())
        raise


def get_relationship_data(
    user_id: str,
    character_id: str,
    db: Session,
    create_if_not_exists: bool = True
) -> Optional[RelationshipData]:
    """관계 데이터 조회"""
    row = db.query(RelationshipTable).filter(
        RelationshipTable.user_id == user_id,
        RelationshipTable.character_id == character_id
    ).first()
    
    if row:
        return row_to_model(row)
    
    # 없으면 생성
    if create_if_not_exists:
        from models.character import CharacterPersona
        from db.character_db import get_character
        
        character = get_character(character_id, db)
        if character:
            new_rel_data = RelationshipData(
                user_id=user_id,
                character_id=character_id,
                intimacy=0.0,
                dominance=Dominance(score=character.dominance_default),
                total_turns=0
            )
            return create_relationship_data(new_rel_data, db)
    
    return None


def create_relationship_data(rel_data: RelationshipData, db: Session) -> RelationshipData:
    """관계 데이터 생성"""
    row = model_to_row(rel_data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row_to_model(row)


def update_relationship_data(rel_data: RelationshipData, db: Session) -> RelationshipData:
    """관계 데이터 업데이트"""
    try:
        row = db.query(RelationshipTable).filter(
            RelationshipTable.user_id == rel_data.user_id,
            RelationshipTable.character_id == rel_data.character_id
        ).first()
        
        if not row:
            return create_relationship_data(rel_data, db)
        
        updated_row = model_to_row(rel_data, row)
        db.commit()
        db.refresh(updated_row)
        return row_to_model(updated_row)
    except Exception as e:
        # 오류 발생 시 롤백
        db.rollback()
        import traceback
        print(f"⚠️ 관계 데이터 업데이트 오류: {e}")
        print(traceback.format_exc())
        # 기존 데이터 반환 시도
        try:
            existing = get_relationship_data(rel_data.user_id, rel_data.character_id, db, create_if_not_exists=False)
            return existing or rel_data
        except:
            return rel_data


# ═══════════════════════════════════════════════════════════
# 스토리 요약 CRUD
# ═══════════════════════════════════════════════════════════

def save_story_summary(
    session_id: str,
    user_id: str,
    location: str,
    turn_number: int,
    turn_id: str,
    user_message: str,
    character_responses: List[Dict],
    character_states: Dict,
    ai_summary: str,
    ai_analysis: str,
    db: Session
) -> StorySummaryTable:
    """스토리 요약 저장"""
    row = StorySummaryTable(
        session_id=session_id,
        user_id=user_id,
        location=location,
        turn_number=turn_number,
        turn_id=turn_id,
        user_message=user_message,
        character_responses=json.dumps(character_responses, ensure_ascii=False),
        character_states=json.dumps(character_states, ensure_ascii=False),
        ai_summary=ai_summary,
        ai_analysis=ai_analysis
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_recent_story_summaries(
    session_id: str,
    limit: int = 5,
    db: Session = None
) -> List[Dict]:
    """최근 스토리 요약 조회"""
    if db is None:
        return []
    
    rows = db.query(StorySummaryTable).filter(
        StorySummaryTable.session_id == session_id
    ).order_by(
        StorySummaryTable.turn_number.desc()
    ).limit(limit).all()
    
    summaries = []
    for row in reversed(rows):  # 오래된 순서로 반환
        summaries.append({
            "turn_number": row.turn_number,
            "turn_id": row.turn_id,
            "user_message": row.user_message,
            "character_responses": json.loads(row.character_responses or "[]"),
            "character_states": json.loads(row.character_states or "{}"),
            "ai_summary": row.ai_summary,
            "ai_analysis": row.ai_analysis,
            "created_at": row.created_at.isoformat() if row.created_at else None
        })
    
    return summaries
