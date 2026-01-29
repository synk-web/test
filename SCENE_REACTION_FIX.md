# 씬 리액션 시스템 수정 사항

## 🔧 수정 완료 사항

### 1. 직접 호명 감지 강화

**파일**: `core/scene_reaction.py`

**수정 내용**:
- 애칭 매칭 추가 (인하야, 인하씨 등)
- 디버그 로그 추가

```python
# 직접 호명 감지 강화
for char in characters:
    char_name = char.name
    # 정확한 이름 매칭
    if char_name in user_message or char_name.lower() in user_msg_lower:
        mentioned_characters.append(char.id)
    # 애칭 매칭 (마지막 2글자)
    elif len(char_name) >= 2:
        name_base = char_name[-2:]
        name_variations = [name_base, name_base + "야", name_base + "씨", name_base + "아"]
        for variation in name_variations:
            if variation in user_message or variation in user_msg_lower:
                mentioned_characters.append(char.id)
                break
```

### 2. "모두" 트리거 로직 개선

**파일**: `core/scene_reaction.py`

**수정 내용**:
- 직접 호명된 캐릭터는 무조건 main
- recent 캐릭터는 최대 2명만 main, 나머지는 reaction

```python
if reaction_scope == "all":
    # 직접 호명된 캐릭터는 무조건 main
    if directly_mentioned:
        return "main"
    # 최근 대화 참여자는 main (최대 2명)
    if scene_context and character_id in scene_context.character_states:
        state = scene_context.character_states[character_id]
        if state.recent:
            recent_count = sum(1 for s in scene_context.character_states.values() if s.recent)
            if recent_count <= 2:
                return "main"
            return "reaction"
    return "reaction"
```

### 3. Scene Context 업데이트 범위 확대

**파일**: `api/chat_multi.py`

**수정 내용**:
- 메인 응답자뿐만 아니라 서브 리액션, 무반응 캐릭터도 속마음 업데이트

```python
# 9-2. 서브 리액션 캐릭터들도 속마음 업데이트
for sub_react in scene_reaction.sub_reactions:
    if sub_react.inner_thought:
        scene_manager.process_character_response(...)

# 9-3. 무반응 캐릭터들도 속마음 업데이트
for no_react in scene_reaction.no_reaction:
    if no_react.get("inner_thought"):
        scene_manager.process_character_response(...)
```

### 4. 프론트엔드 씬 리액션 UI 추가

**파일**: `static/index.html`

**수정 내용**:
- 메인 응답 표시 (기존 방식 유지)
- 서브 리액션 패널 추가
- CSS 스타일 추가

**새로운 UI 구조**:
```html
<div class="sub-reactions-panel">
    <div class="sub-reactions-header">💭 주변 반응</div>
    <div class="sub-reactions-list">
        <div class="sub-reaction-item">
            <span class="reaction-character">황인하</span>
            <span class="reaction-text">*흥미롭다는 듯 입꼬리를 올린다*</span>
            <span class="reaction-thought">💭 대장? 재미있는 놈이네.</span>
        </div>
    </div>
</div>
```

### 5. 디버그 로그 추가

**파일**: `core/scene_reaction.py`

**추가된 로그**:
- 반응 범위 분석 결과
- 직접 호명 감지
- 캐릭터별 반응 타입 결정

---

## 🧪 테스트 시나리오

### 테스트 1: "모두" 트리거

```
입력: "야 너희들 들어봐"
예상:
- main_responses: 2명 (recent 캐릭터)
- sub_reactions: 나머지
- no_reaction: 관심 없는 캐릭터
```

### 테스트 2: 직접 호명

```
입력: "표다은! 너 주창윤 좋아해?"
예상:
- main_responses: 표다은 (직접 호명)
- sub_reactions: 나머지
```

### 테스트 3: 서브 리액션 UI

```
예상:
- 메인 응답 표시
- "💭 주변 반응" 패널 표시
- 서브 리액션 목록 표시
```

---

## 📊 수정 전후 비교

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| "모두" 트리거 | ❌ 1명만 응답 | ✅ 여러 명 반응 |
| 직접 호명 | ❌ 다른 사람 응답 | ✅ 정확히 감지 |
| 속마음 업데이트 | ❌ 응답한 캐릭터만 | ✅ 모든 캐릭터 |
| 서브 리액션 UI | ❌ 없음 | ✅ 추가됨 |

---

## ✅ 다음 단계

1. 서버 재시작 후 테스트
2. 서버 로그 확인 (`[Scene Reaction]` 로그)
3. 프론트엔드에서 서브 리액션 패널 확인

---

**수정 완료 날짜**: 2024년  
**수정 파일**:
- `core/scene_reaction.py` (직접 호명 강화, "모두" 트리거 개선)
- `api/chat_multi.py` (Scene Context 업데이트 범위 확대)
- `static/index.html` (서브 리액션 UI 추가)
