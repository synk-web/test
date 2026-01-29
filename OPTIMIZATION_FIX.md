# 최적화 후 API 키 로드 문제 해결

## 🔍 문제 원인

최적화 과정에서 `.env` 파일 로드 방식이 변경되면서 발생한 문제:

### 최적화 전 (정상 작동)
```python
# api/chat_multi.py
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)  # override 파라미터 없음

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
```

### 최적화 후 (문제 발생)
```python
# utils/config.py
result = load_dotenv(dotenv_path=str(env_path), override=True)  # override=True 추가
```

**문제점:**
1. `override=True`로 인해 이미 설정된 환경 변수를 덮어쓸 수 있음
2. 싱글톤 패턴으로 인해 초기화 시점이 달라질 수 있음
3. 모듈 임포트 순서에 따라 `.env` 파일이 로드되지 않을 수 있음

## ✅ 해결 방법

최적화 전 방식과 **완전히 동일**하게 동작하도록 수정:

### 수정된 코드

#### `utils/config.py`
```python
def load_env(project_root: str = None) -> None:
    # 최적화 전 방식과 완전히 동일: override 없이 로드
    # 최적화 전: load_dotenv(dotenv_path=env_path) - override 파라미터 없음
    result = load_dotenv(dotenv_path=str(env_path))
    # 최적화 전에는 로드 결과를 확인하지 않았으므로 여기서도 조용히 처리
```

#### `utils/gemini_client.py`
```python
def __init__(self):
    if not GeminiClient._initialized:
        # 최적화 전 방식과 동일
        load_env()
        
        # 최적화 전: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        api_key = get_gemini_api_key()
        
        if api_key:
            # 최적화 전: genai.configure(api_key=GEMINI_API_KEY)
            genai.configure(api_key=api_key)
            # ...
```

## 🔄 변경 사항

1. **`load_dotenv` 호출 방식 변경**
   - `override=True` → `override` 파라미터 제거 (최적화 전과 동일)
   - 불필요한 로그 제거

2. **초기화 로직 유지**
   - 싱글톤 패턴은 유지하되, 로드 방식만 최적화 전과 동일하게 변경

## 🧪 테스트 결과

```
✅ Gemini API 키 로드됨: AIzaSyBEAH...wtlOw (길이: 39)
✅ 정상적으로 API 키가 로드되었습니다.
```

## 📝 참고사항

- 최적화 전후 모두 `.env` 파일에서 동일한 키를 읽음
- 경로 계산 방식은 다르지만 결과는 동일
- `load_dotenv`의 `override` 파라미터가 핵심 차이점

## ⚠️ 중요

만약 여전히 API 키 정지 오류가 발생한다면:
1. `.env` 파일의 API 키가 실제로 정지되었을 수 있음
2. 새로운 API 키를 발급받아 `.env` 파일을 업데이트
3. 서버 재시작

코드는 이제 최적화 전과 동일하게 동작하므로, API 키 자체의 문제일 가능성이 높습니다.
