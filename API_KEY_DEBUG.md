# API 키 디버깅 가이드

## 🔍 현재 상태 확인

서버를 실행하면 다음 로그가 표시됩니다:

```
✅ .env 파일 로드됨: /path/to/.env
✅ Gemini API 키 로드됨: AIzaSyXXXX...XXXXX (길이: 39)
```

이 로그를 통해 실제로 사용 중인 API 키를 확인할 수 있습니다.

## ❌ API 키 정지 오류 해결

### 1. 오류 메시지 확인
오류 메시지에 나온 API 키가 `.env` 파일의 키와 일치하는지 확인:
- 오류: `Consumer 'api_key:AIzaSyBEAHWVj-H2g_GjvYxjua2kGVawFewtlOw' has been suspended`
- `.env` 파일의 키와 비교

### 2. 새 API 키 발급
1. https://aistudio.google.com/ 접속
2. "Get API Key" → "Create API Key"
3. 새 API 키 복사

### 3. .env 파일 업데이트
```env
GEMINI_API_KEY=새로운_API_키_여기에_붙여넣기
```

### 4. 서버 재시작
**중요**: 싱글톤 패턴 때문에 서버를 재시작해야 새 API 키가 적용됩니다.

```bash
# 서버 중지 후 재시작
python main.py
```

## 🔄 API 키 재로드 (서버 재시작 없이)

서버를 재시작하지 않고 API 키를 변경하려면:

```python
from utils.gemini_client import gemini_client

# API 키 재로드
gemini_client.reload_api_key()
```

하지만 **권장하지 않습니다**. 서버를 재시작하는 것이 더 안전합니다.

## 📝 디버깅 체크리스트

- [ ] `.env` 파일이 프로젝트 루트에 있는가?
- [ ] `GEMINI_API_KEY=` 형식이 정확한가? (공백 없음)
- [ ] API 키 앞뒤에 따옴표나 공백이 없는가?
- [ ] 서버를 재시작했는가?
- [ ] 서버 로그에서 올바른 API 키가 로드되었는지 확인했는가?

## 🚨 주의사항

1. **싱글톤 패턴**: `GeminiClient`는 한 번만 초기화되므로, `.env` 파일을 변경한 후에는 **반드시 서버를 재시작**해야 합니다.

2. **API 키 보안**: 
   - 절대 Git에 커밋하지 마세요
   - `.gitignore`에 `.env` 추가
   - 로그에 전체 API 키가 표시되지 않도록 마스킹 처리됨

3. **오류 메시지**: 
   - API 키 정지 오류는 Google에서 해당 키를 사용 중지한 것입니다
   - 새로운 API 키를 발급받아야 합니다
