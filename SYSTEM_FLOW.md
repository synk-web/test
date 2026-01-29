# 🔄 SYNK MVP 시스템 흐름도

## 📊 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    사용자 입력 → 캐릭터 응답                      │
└─────────────────────────────────────────────────────────────────┘

[프론트엔드] → [API] → [Speaker Selector] → [Prompt Builder] → [Gemini API] → [응답]
```

---

## 🎯 단계별 상세 흐름

### **1단계: 사용자 입력 (프론트엔드)**

**파일:** `static/index.html`

```javascript
// 함수: sendMessage()
async function sendMessage() {
    // 1. 사용자 메시지 가져오기
    const message = input.value.trim();
    
    // 2. API 호출
    const response = await fetch(`/api/chat/location/${currentLocationId}`, {
        method: 'POST',
        body: JSON.stringify({
            user_id: currentUserId,
            location_id: currentLocationId,
            message: message,
            session_id: sessionId
        })
    });
}
```

**입력 데이터:**
- `user_id`: 사용자 ID
- `location_id`: 현재 장소 (예: "베타_동_로비")
- `message`: 사용자 메시지 (예: "안녕!")
- `session_id`: 대화 세션 ID

---

### **2단계: API 엔드포인트 (백엔드)**

**파일:** `api/chat_multi.py`

**함수:** `chat_in_location()`

```python
@router.post("/location/{location_id}")
async def chat_in_location(location_id, request, db):
    # 1️⃣ 장소 확인
    location = get_location(location_id, db)
    
    # 2️⃣ 장소의 캐릭터들 조회
    characters = get_characters_by_location(location_id, db)
    # → [주창윤, 황인하, 표다은, 민아름, 고선하]
    
    # 3️⃣ 대화 히스토리 가져오기/생성
    history = conversation_histories[session_id]
    
    # 4️⃣ 유저 메시지 히스토리에 추가
    history.add_turn("user", request.message)
    
    # 5️⃣ Speaker Selector로 응답할 캐릭터 선택 ⭐ 핵심!
    speaking_character = select_speaker(
        message=request.message,
        characters=characters,
        history=history,
        intervention_probability=0.2
    )
    # → 예: 주창윤 선택됨
    
    # 6️⃣ 프롬프트 생성
    full_prompt = build_full_prompt(...)
    
    # 7️⃣ Gemini API 호출
    character_response = generate_response(full_prompt)
    
    # 8️⃣ 응답 히스토리에 추가
    history.add_turn(speaking_character.id, character_response)
    
    # 9️⃣ 응답 반환
    return MultiChatResponse(...)
```

---

### **3단계: Speaker Selector Logic (누가 응답할지 결정)**

**파일:** `core/speaker_selector.py`

**함수:** `select_speaker()`

```python
def select_speaker(message, characters, history, intervention_probability):
    """
    규칙 1: 지명(Mention) 감지
    """
    mentioned = detect_mention(message, characters)
    # → "주창윤" 이름이 메시지에 있으면 주창윤 반환
    
    if mentioned:
        return mentioned
    
    """
    규칙 2: 문맥(Context) 기반
    """
    if history.last_speaker:
        # 마지막에 말한 캐릭터 찾기
        last_char = find_character(history.last_speaker, characters)
        
        """
        규칙 3: 랜덤 난입(Intervention)
        """
        if history.get_turn_count() >= 3:
            if random.random() < 0.2:  # 20% 확률
                # 다른 캐릭터 중 랜덤 선택
                return random.choice(other_characters)
        
        return last_char
    
    # 기본값: 첫 번째 캐릭터
    return characters[0]
```

**예시 시나리오:**

| 사용자 입력 | 규칙 | 선택된 캐릭터 | 이유 |
|------------|------|--------------|------|
| "주창윤아 안녕!" | 지명 | 주창윤 | 이름 언급 |
| "뭐해?" | 문맥 | 주창윤 | 마지막 화자가 주창윤 |
| "그래?" (3턴째) | 랜덤 난입 | 황인하 | 20% 확률로 다른 캐릭터 |

---

### **4단계: 프롬프트 생성**

**파일:** `api/chat_multi.py` + `core/speaker_selector.py`

**함수들:**

```python
# 4-1. 캐릭터 페르소나
character_prompt = speaking_character.to_prompt()
# → "이름: 주창윤\n성격: 오만하고 건방진...\n말투: 재수 없는 반말..."

# 4-2. 멀티 캐릭터 컨텍스트
multi_context = build_multi_character_context(
    characters=characters,
    speaking_character=speaking_character,
    location=location.name
)
# → "[함께 있는 인물]\n- 황인하: 살벌한 독설가...\n- 표다은: 눈치 빠른 참모..."

# 4-3. 대화 히스토리 컨텍스트
conversation_context = build_conversation_context(history, characters)
# → "[최근 대화]\n유저: 안녕!\n주창윤: 하... 뭐야?"

# 4-4. 최종 프롬프트 조합
full_prompt = f"""
당신은 '{speaking_character.name}'입니다.

{character_prompt}
{multi_context}
{conversation_context}

[현재 대화]
유저: {request.message}

[응답 지침]
- 캐릭터의 말투와 성격을 100% 유지하세요.
- 자연스러운 그룹 대화의 일부처럼 반응하세요.
"""
```

**생성된 프롬프트 예시:**

```
당신은 '주창윤'입니다.

[캐릭터 정보]
이름: 주창윤
성격: 오만하고 건방진 재벌 2세...
말투: 재수 없는 반말. 비꼬는 말투...

[현재 장소: 베타 동 로비]

[함께 있는 인물]
- 황인하: 살벌한 독설가이자 빌런과 여왕...
- 표다은: 눈치 빠르고 똑똑한 참모...

[최근 대화]
유저: 안녕!
주창윤: 하... 뭐야?

[현재 대화]
유저: 뭐해?

[응답 지침]
- 캐릭터의 말투와 성격을 100% 유지하세요.
- 자연스러운 그룹 대화의 일부처럼 반응하세요.
```

---

### **5단계: Gemini API 호출**

**파일:** `api/chat_multi.py`

```python
# Gemini 모델 생성
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# 프롬프트로 응답 생성
response = model.generate_content(full_prompt)
character_response = response.text.strip()
# → "하... 거지 같네. 뭐 하긴, 여기서 놀고 있지."
```

---

### **6단계: 응답 처리 및 반환**

**파일:** `api/chat_multi.py`

```python
# 1. 응답을 히스토리에 추가
history.add_turn(
    speaker=speaking_character.id,
    message=character_response,
    character_name=speaking_character.name
)

# 2. 응답 객체 생성
return MultiChatResponse(
    turn_id=turn_id,
    session_id=session_id,
    character_id=speaking_character.id,
    character_name=speaking_character.name,
    character_response=character_response,
    location=location.name,
    all_characters=all_characters_info,
    conversation_turn=history.get_turn_count()
)
```

---

### **7단계: 프론트엔드 응답 표시**

**파일:** `static/index.html`

```javascript
// 함수: sendMessage() (계속)
const data = await response.json();

// 캐릭터 응답을 화면에 표시
addMessage(
    'character', 
    data.character_response,  // "하... 거지 같네..."
    data.character_name,      // "주창윤"
    data.character_id,        // "npc_joo_changyun"
    data.conversation_turn    // 3
);
```

---

## 🔑 핵심 함수 요약

| 단계 | 파일 | 함수 | 역할 |
|------|------|------|------|
| **입력** | `static/index.html` | `sendMessage()` | 사용자 메시지 전송 |
| **API** | `api/chat_multi.py` | `chat_in_location()` | 요청 처리 및 응답 생성 |
| **선택** | `core/speaker_selector.py` | `select_speaker()` | 응답할 캐릭터 결정 |
| **선택** | `core/speaker_selector.py` | `detect_mention()` | 이름 언급 감지 |
| **컨텍스트** | `core/speaker_selector.py` | `build_conversation_context()` | 대화 히스토리 문자열 생성 |
| **컨텍스트** | `core/speaker_selector.py` | `build_multi_character_context()` | 멀티 캐릭터 정보 생성 |
| **프롬프트** | `models/character.py` | `to_prompt()` | 캐릭터 페르소나 프롬프트 생성 |
| **생성** | `api/chat_multi.py` | `genai.GenerativeModel()` | Gemini API 호출 |
| **표시** | `static/index.html` | `addMessage()` | 화면에 메시지 표시 |

---

## 📝 데이터 흐름 예시

### 입력: "주창윤아 안녕!"

```
1. 프론트엔드
   └─ sendMessage() 
      └─ POST /api/chat/location/베타_동_로비
         {user_id, location_id, message: "주창윤아 안녕!", session_id}

2. API 엔드포인트
   └─ chat_in_location()
      ├─ get_characters_by_location() → [주창윤, 황인하, ...]
      ├─ history.add_turn("user", "주창윤아 안녕!")
      └─ select_speaker()
         ├─ detect_mention() → 주창윤 발견! ✅
         └─ return 주창윤

3. 프롬프트 생성
   └─ build_full_prompt()
      ├─ character.to_prompt() → "이름: 주창윤..."
      ├─ build_multi_character_context() → "함께 있는 인물: 황인하..."
      └─ build_conversation_context() → "최근 대화: ..."

4. Gemini API
   └─ model.generate_content(full_prompt)
      └─ "하... 뭐야, 너? 또 왔어?"

5. 응답 처리
   └─ history.add_turn("npc_joo_changyun", "하... 뭐야, 너? 또 왔어?")
   └─ return MultiChatResponse(...)

6. 프론트엔드 표시
   └─ addMessage('character', "하... 뭐야, 너? 또 왔어?", "주창윤")
```

---

## 🎮 Speaker Selector Logic 상세

### 규칙 우선순위

```
1순위: 지명(Mention)
   └─ "주창윤아!" → 주창윤 응답

2순위: 문맥(Context)
   └─ "뭐해?" → 마지막 화자(주창윤) 응답

3순위: 랜덤 난입(Intervention)
   └─ 3턴 이상 + 20% 확률 → 다른 캐릭터(황인하) 응답

4순위: 기본값
   └─ 첫 번째 캐릭터 응답
```

---

## 💾 데이터 저장 위치

- **대화 히스토리:** `conversation_histories` (메모리, `api/chat_multi.py`)
- **캐릭터 데이터:** `synk_mvp.db` → `characters` 테이블
- **장소 데이터:** `synk_mvp.db` → `locations` 테이블

---

## 🔄 전체 흐름 다이어그램

```
[사용자] "주창윤아 안녕!"
    ↓
[프론트엔드] sendMessage()
    ↓ POST /api/chat/location/베타_동_로비
[API] chat_in_location()
    ↓
[DB] get_characters_by_location() → [주창윤, 황인하, ...]
    ↓
[Speaker Selector] select_speaker()
    ├─ detect_mention() → 주창윤 발견 ✅
    └─ return 주창윤
    ↓
[Prompt Builder] build_full_prompt()
    ├─ character.to_prompt()
    ├─ build_multi_character_context()
    └─ build_conversation_context()
    ↓
[Gemini API] generate_content()
    ↓ "하... 뭐야, 너?"
[API] history.add_turn() + return Response
    ↓
[프론트엔드] addMessage()
    ↓
[화면] "주창윤: 하... 뭐야, 너?"
```

---

이제 전체 시스템의 흐름을 이해하셨나요? 🎯
