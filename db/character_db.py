"""
캐릭터 데이터베이스
SYNK MVP - 캐릭터 저장/조회
"""
import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from models.character import CharacterPersona, Location

Base = declarative_base()


class CharacterTable(Base):
    """캐릭터 테이블"""
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False, index=True)
    
    # JSON 필드
    personality = Column(Text)
    speech_style = Column(Text)
    speech_examples = Column(Text)  # JSON array
    background = Column(Text)
    secrets = Column(Text)  # JSON array
    
    user_relationship = Column(String, default="stranger")
    dominance_default = Column(Float, default=0.0)
    
    emotion_triggers = Column(Text)  # JSON object
    sensitive_topics = Column(Text)  # JSON array
    
    tags = Column(Text)  # JSON array
    ability = Column(String)
    ability_rank = Column(String)
    
    default_emotion = Column(String, default="neutral")
    default_posture = Column(String, default="standing")
    voice_tone = Column(String, default="normal")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LocationTable(Base):
    """장소 테이블"""
    __tablename__ = "locations"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    atmosphere = Column(Text)
    tags = Column(Text)  # JSON array
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# DB 연결
from utils.config import get_database_url

DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_character_db():
    """캐릭터 DB 초기화"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """DB 세션"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# 캐릭터 CRUD
# ═══════════════════════════════════════════════════════════

def character_to_model(row: CharacterTable) -> CharacterPersona:
    """테이블 → 모델 변환"""
    return CharacterPersona(
        id=row.id,
        name=row.name,
        location=row.location,
        personality=row.personality or "",
        speech_style=row.speech_style or "",
        speech_examples=json.loads(row.speech_examples or "[]"),
        background=row.background or "",
        secrets=json.loads(row.secrets or "[]"),
        user_relationship=row.user_relationship or "stranger",
        dominance_default=row.dominance_default or 0.0,
        emotion_triggers=json.loads(row.emotion_triggers or "{}"),
        sensitive_topics=json.loads(row.sensitive_topics or "[]"),
        tags=json.loads(row.tags or "[]"),
        ability=row.ability,
        ability_rank=row.ability_rank,
        default_emotion=row.default_emotion or "neutral",
        default_posture=row.default_posture or "standing",
        voice_tone=row.voice_tone or "normal",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def model_to_row(char: CharacterPersona, existing: CharacterTable = None) -> CharacterTable:
    """모델 → 테이블 변환"""
    row = existing or CharacterTable()
    
    row.id = char.id
    row.name = char.name
    row.location = char.location
    row.personality = char.personality
    row.speech_style = char.speech_style
    row.speech_examples = json.dumps(char.speech_examples, ensure_ascii=False)
    row.background = char.background
    row.secrets = json.dumps(char.secrets, ensure_ascii=False)
    row.user_relationship = char.user_relationship
    row.dominance_default = char.dominance_default
    row.emotion_triggers = json.dumps(char.emotion_triggers, ensure_ascii=False)
    row.sensitive_topics = json.dumps(char.sensitive_topics, ensure_ascii=False)
    row.tags = json.dumps(char.tags, ensure_ascii=False)
    row.ability = char.ability
    row.ability_rank = char.ability_rank
    row.default_emotion = char.default_emotion
    row.default_posture = char.default_posture
    row.voice_tone = char.voice_tone
    row.updated_at = datetime.now()
    
    return row


def create_character(char: CharacterPersona, db: Session) -> CharacterPersona:
    """캐릭터 생성"""
    row = model_to_row(char)
    row.created_at = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return character_to_model(row)


def get_character(character_id: str, db: Session) -> Optional[CharacterPersona]:
    """캐릭터 조회"""
    row = db.query(CharacterTable).filter(CharacterTable.id == character_id).first()
    if not row:
        return None
    return character_to_model(row)


def get_characters_by_location(location: str, db: Session) -> List[CharacterPersona]:
    """특정 장소의 캐릭터들 조회"""
    rows = db.query(CharacterTable).filter(CharacterTable.location == location).all()
    return [character_to_model(row) for row in rows]


def get_all_characters(db: Session) -> List[CharacterPersona]:
    """모든 캐릭터 조회"""
    rows = db.query(CharacterTable).all()
    return [character_to_model(row) for row in rows]


def update_character(character_id: str, updates: dict, db: Session) -> Optional[CharacterPersona]:
    """캐릭터 수정"""
    row = db.query(CharacterTable).filter(CharacterTable.id == character_id).first()
    if not row:
        return None
    
    # 업데이트할 필드들
    for key, value in updates.items():
        if hasattr(row, key):
            if key in ["speech_examples", "secrets", "sensitive_topics", "tags"]:
                setattr(row, key, json.dumps(value, ensure_ascii=False))
            elif key == "emotion_triggers":
                setattr(row, key, json.dumps(value, ensure_ascii=False))
            else:
                setattr(row, key, value)
    
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return character_to_model(row)


def delete_character(character_id: str, db: Session) -> bool:
    """캐릭터 삭제"""
    row = db.query(CharacterTable).filter(CharacterTable.id == character_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


# ═══════════════════════════════════════════════════════════
# 장소 CRUD
# ═══════════════════════════════════════════════════════════

def create_location(loc: Location, db: Session) -> Location:
    """장소 생성"""
    row = LocationTable(
        id=loc.id,
        name=loc.name,
        description=loc.description,
        atmosphere=loc.atmosphere,
        tags=json.dumps(loc.tags, ensure_ascii=False),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return loc


def get_location(location_id: str, db: Session) -> Optional[Location]:
    """장소 조회"""
    row = db.query(LocationTable).filter(LocationTable.id == location_id).first()
    if not row:
        return None
    return Location(
        id=row.id,
        name=row.name,
        description=row.description or "",
        atmosphere=row.atmosphere or "",
        tags=json.loads(row.tags or "[]"),
    )


def get_all_locations(db: Session) -> List[Location]:
    """모든 장소 조회"""
    rows = db.query(LocationTable).all()
    return [
        Location(
            id=row.id,
            name=row.name,
            description=row.description or "",
            atmosphere=row.atmosphere or "",
            tags=json.loads(row.tags or "[]"),
        )
        for row in rows
    ]
