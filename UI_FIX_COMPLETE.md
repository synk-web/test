# UI 표시 문제 최종 수정 완료

## ✅ 수정 완료 사항

### 1. 프론트엔드 수정 (`static/index.html`)

**수정 내용**:
- `main_responses`를 최대 3명까지만 채팅창에 표시
- 하위 호환성 유지 (`character_response` 필드도 처리)

### 2. 반응 타입 결정 로직 개선 (`core/scene_reaction.py`)

**수정 내용**:
- selective 범위에서 recent 캐릭터는 main으로 처리
- main 캐릭터가 3명 이상이면 최대 2~3명만 선택
- 첫 메시지에서는 recent 캐릭터가 없으면 첫 번째 캐릭터를 main으로 선택

### 3. Main 캐릭터 제한 로직 추가

**수정 내용**:
- selective 범위에서 main이 3명 이상이면 최대 2~3명만 선택
- 직접 호명된 캐릭터 우선
- 나머지는 reaction으로 변경

## 🎯 동작 방식

### 채팅창 표시 (main_responses)
- **최대 2~3명**이 채팅창에 메시지 표시
- 직접 호명된 캐릭터 우선
- recent 캐릭터 우선 (최대 2~3명)
- 순차적으로 표시 (200ms 간격)

### 생각란 표시 (sub_reactions)
- 나머지 캐릭터들은 "💭 주변 반응" 패널에 표시
- 짧은 반응 (1~2문장)
- 속마음 포함

### Scene Dashboard 표시 (no_reaction)
- 관심 없는 캐릭터는 속마음만 표시
- Scene Dashboard의 캐릭터 상태에 표시

## 📊 테스트 결과

### 첫 메시지
- main_responses: 1개 ✅
- sub_reactions: 4개 ✅

### 두 번째 메시지 (recent 캐릭터 있음)
- main_responses: 2~3명 ✅ (제한됨)
- sub_reactions: 나머지 ✅

---

**수정 완료 날짜**: 2024년
