# 데이터베이스 사용 가이드

## 📋 현재 사용 중인 데이터베이스

### SQLite 기반 (현재 사용 중)
- **파일**: `synk_mvp.db` (프로젝트 루트)
- **테이블**:
  - `characters` - 캐릭터 정보
  - `locations` - 장소 정보
  - `relationships` - 유저-캐릭터 관계 데이터
  - `user_profiles` - 유저 프로필
  - `story_summaries` - 스토리 요약

### Supabase (비활성화)
- 현재 주석 처리되어 있음
- 향후 필요 시 활성화 가능

## 🗂️ 데이터베이스 파일 구조

```
db/
├── character_db.py      ✅ 사용 중 - 캐릭터/장소 (SQLite)
├── database.py          ✅ 사용 중 - 관계/프로필/요약 (SQLite)
├── user_profile_db.py   ✅ 사용 중 - 유저 프로필 (SQLite)
└── supabase_db.py       ❌ 비활성화 - Supabase 연동
```

## 🌱 캐릭터 데이터 시딩

### 시딩 스크립트
**파일**: `scripts/seed_characters.py`

### 실행 방법
```bash
python scripts/seed_characters.py
```

### 시딩되는 데이터

#### 장소 (4개)
1. **베타 동 로비** - 빌런과 기숙사 1층 로비
2. **지하 훈련장** - 전투 훈련 시설
3. **아카데미 정문** - 히어로 아카데미 정문
4. **의무실** - 부상자 치료 시설

#### 캐릭터 (9명)

**베타 동 로비 (5명)**
- 주창윤 - 오만한 재벌 2세 (투명화, C급)
- 황인하 - 살벌한 독설가 여왕 (베놈, A급)
- 표다은 - 눈치 빠른 서포터 (화염방사, D급)
- 민아름 - 잠꾸러기 (나이트메어, B급)
- 고선하 - 결벽증 공주병 (염동력, B급)

**지하 훈련장 (2명)**
- 신채린 - 광기 어린 마법소녀 (롤리폴리, S급)
- 권우미 - 싸움 구경 좋아하는 교수 (뇌신, S급)

**아카데미 정문 (1명)**
- 이가은 - User바라기 소꿉친구 (가속, A급)

**의무실 (1명)**
- 심나은 - 만사 귀찮은 담임 (섀도우, S급)

## 🔄 데이터베이스 초기화

### 자동 초기화
서버 시작 시 (`main.py`):
```python
init_db()  # relationships, user_profiles, story_summaries 테이블 생성
init_character_db()  # characters, locations 테이블 생성
```

### 수동 초기화
```python
from db.character_db import init_character_db
from db.database import init_db

init_db()
init_character_db()
```

## 📊 데이터베이스 사용 예시

### 캐릭터 조회
```python
from db.character_db import get_characters_by_location, SessionLocal

db = SessionLocal()
characters = get_characters_by_location("베타_동_로비", db)
db.close()
```

### 관계 데이터 조회
```python
from db.database import get_relationship_data, SessionLocal

db = SessionLocal()
rel_data = get_relationship_data("user_123", "npc_joo_changyun", db)
db.close()
```

## 🔍 데이터베이스 확인

### SQLite 브라우저로 확인
```bash
# DB 파일 위치
./synk_mvp.db

# 또는 Python으로 확인
python -c "from db.character_db import SessionLocal, CharacterTable; db = SessionLocal(); print([c.name for c in db.query(CharacterTable).all()]); db.close()"
```

## 📝 주요 함수 정리

### character_db.py
- `init_character_db()` - 테이블 생성
- `create_character()` - 캐릭터 생성
- `get_character()` - 캐릭터 조회
- `get_characters_by_location()` - 장소별 캐릭터 조회
- `create_location()` - 장소 생성
- `get_location()` - 장소 조회

### database.py
- `init_db()` - 테이블 생성
- `get_relationship_data()` - 관계 데이터 조회
- `update_relationship_data()` - 관계 데이터 업데이트
- `get_user_profile()` - 유저 프로필 조회
- `save_story_summary()` - 스토리 요약 저장

## ⚠️ 주의사항

1. **세션 관리**: `SessionLocal()`로 생성한 세션은 반드시 `close()` 호출
2. **JSON 필드**: SQLite TEXT 타입에 JSON 문자열로 저장
3. **중복 체크**: 시딩 스크립트는 중복을 체크하므로 안전하게 재실행 가능
4. **데이터베이스 파일**: `.gitignore`에 포함되어 Git에 커밋되지 않음
