# 데이터베이스 구조 문서

## 📁 데이터베이스 파일 구조

```
db/
├── character_db.py      # 캐릭터 및 장소 데이터 (SQLite)
├── database.py          # 관계 데이터, 유저 프로필, 스토리 요약 (SQLite)
├── user_profile_db.py   # 유저 프로필 관리 (SQLite)
└── supabase_db.py       # Supabase 연동 (현재 비활성화)
```

## 🗄️ 데이터베이스 테이블

### 1. 캐릭터 & 장소 (`character_db.py`)

**데이터베이스**: `synk_mvp.db` (SQLite)

#### `characters` 테이블
- 캐릭터 기본 정보 및 페르소나
- JSON 필드: `speech_examples`, `secrets`, `emotion_triggers`, `sensitive_topics`, `tags`
- 초기 데이터: `scripts/seed_characters.py`로 시딩

#### `locations` 테이블
- 장소 정보
- JSON 필드: `tags`
- 초기 데이터: `scripts/seed_characters.py`로 시딩

**사용 위치:**
- `api/character_api.py` - 캐릭터 CRUD
- `api/chat_multi.py` - 캐릭터 조회
- `api/opening.py` - 장소별 캐릭터 조회

### 2. 관계 데이터 (`database.py`)

**데이터베이스**: `synk_mvp.db` (SQLite)

#### `relationships` 테이블
- 유저와 캐릭터 간의 관계 데이터
- 친밀도, Dominance, 감정 통계, 핵심 기억, 트리거 키워드
- JSON 필드: `dominance_history`, `emotional_stats`, `core_memories`, `trigger_keywords`

**사용 위치:**
- `api/reaction.py` - 이모지 리액션으로 관계 데이터 업데이트
- `core/data_collector.py` - 대화 데이터 수집 및 관계 업데이트
- `core/memory_manager.py` - 핵심 기억 관리

#### `user_profiles` 테이블
- 유저 프로필 정보
- JSON 필드: `personality_traits`, `character_impressions`, `key_actions`, `mentioned_facts`, `likes`, `dislikes`

**사용 위치:**
- `api/user_profile.py` - 유저 프로필 CRUD
- `core/user_profile_extractor.py` - 유저 정보 추출

#### `story_summaries` 테이블
- 대화 내용 및 AI 분석 요약
- JSON 필드: `key_events`

**사용 위치:**
- `core/story_analyzer.py` - 스토리 분석 및 요약

### 3. 유저 프로필 (`user_profile_db.py`)

**데이터베이스**: `synk_mvp.db` (SQLite)

`database.py`의 `user_profiles` 테이블과 동일한 테이블 사용 (별도 파일로 관리)

## 🌱 데이터 시딩

### 캐릭터 및 장소 시딩

**스크립트**: `scripts/seed_characters.py`

**실행 방법:**
```bash
python scripts/seed_characters.py
```

**시딩되는 데이터:**
- 장소: 4개
  - 베타 동 로비
  - 지하 훈련장
  - 아카데미 정문
  - 의무실
- 캐릭터: 9명
  - 베타 동 로비: 5명 (주창윤, 황인하, 표다은, 민아름, 고선하)
  - 지하 훈련장: 2명 (신채린, 권우미)
  - 아카데미 정문: 1명 (이가은)
  - 의무실: 1명 (심나은)

**중복 체크:**
- 이미 존재하는 캐릭터/장소는 건너뜀
- 안전하게 여러 번 실행 가능

## 🔄 데이터베이스 초기화

### 서버 시작 시 자동 초기화

`main.py`의 `startup_event()`에서:
```python
init_db()  # 관계 데이터 DB (relationships, user_profiles, story_summaries)
init_character_db()  # 캐릭터 DB (characters, locations)
```

### 수동 초기화

```python
from db.character_db import init_character_db
from db.database import init_db

init_db()
init_character_db()
```

## 📊 데이터베이스 파일 위치

- **SQLite 파일**: `synk_mvp.db` (프로젝트 루트)
- **설정**: `utils/config.py`의 `get_database_url()`에서 관리
- 기본값: `sqlite:///./synk_mvp.db`

## 🔗 데이터 흐름

```
1. 서버 시작
   └─→ init_db() + init_character_db()
       └─→ 테이블 생성 (없으면)

2. 캐릭터 시딩 (선택사항)
   └─→ python scripts/seed_characters.py
       └─→ 캐릭터 및 장소 데이터 삽입

3. 채팅 시작
   └─→ api/chat_multi.py
       ├─→ character_db.py: 캐릭터 조회
       ├─→ database.py: 관계 데이터 조회/생성
       └─→ database.py: 스토리 요약 저장

4. 이모지 리액션
   └─→ api/reaction.py
       └─→ database.py: 관계 데이터 업데이트
```

## 📝 주요 함수

### character_db.py
- `init_character_db()` - 캐릭터 DB 초기화
- `create_character()` - 캐릭터 생성
- `get_character()` - 캐릭터 조회
- `get_characters_by_location()` - 장소별 캐릭터 조회
- `create_location()` - 장소 생성
- `get_location()` - 장소 조회

### database.py
- `init_db()` - 관계 데이터 DB 초기화
- `get_relationship_data()` - 관계 데이터 조회
- `update_relationship_data()` - 관계 데이터 업데이트
- `get_user_profile()` - 유저 프로필 조회
- `update_user_profile()` - 유저 프로필 업데이트
- `save_story_summary()` - 스토리 요약 저장

## ⚠️ 주의사항

1. **데이터베이스 파일**: `.gitignore`에 포함되어 Git에 커밋되지 않음
2. **시딩 스크립트**: 여러 번 실행해도 안전 (중복 체크 포함)
3. **JSON 필드**: SQLite의 TEXT 타입에 JSON 문자열로 저장
4. **세션 관리**: SQLAlchemy SessionLocal 사용, 사용 후 반드시 close()

## 🔄 마이그레이션 (향후 Supabase 전환 시)

Supabase로 전환할 때:
1. `supabase_schema.sql` 실행
2. `db/supabase_db.py` 사용
3. `db/character_db.py`, `db/database.py`는 SQLite용으로 유지 또는 제거
