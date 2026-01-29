# Gemini API 키 설정 가이드

## 🔑 API 키 발급 방법

### 1. Google AI Studio 접속
- URL: https://aistudio.google.com/
- Google 계정으로 로그인

### 2. API 키 생성
1. 좌측 메뉴에서 "Get API Key" 클릭
2. "Create API Key" 선택
3. 새 프로젝트 생성 또는 기존 프로젝트 선택
4. API 키 복사

### 3. .env 파일에 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 형식으로 저장:

```env
GEMINI_API_KEY=your_api_key_here
```

**중요:**
- `.env` 파일은 Git에 커밋하지 마세요 (`.gitignore`에 추가 권장)
- API 키 앞뒤에 따옴표나 공백이 없어야 합니다
- `GEMINI_API_KEY`는 대문자로 작성해야 합니다

## ❌ API 키 오류 해결

### 오류: "API 키가 정지되었습니다"
- **원인**: API 키가 Google에 의해 정지됨
- **해결**: 
  1. Google AI Studio에서 새로운 API 키 발급
  2. `.env` 파일의 `GEMINI_API_KEY` 값 업데이트
  3. 서버 재시작

### 오류: "API 키가 유효하지 않습니다"
- **원인**: 
  - API 키가 잘못 입력됨
  - `.env` 파일이 올바른 위치에 없음
  - API 키 형식이 잘못됨
- **해결**:
  1. `.env` 파일이 프로젝트 루트에 있는지 확인
  2. API 키 앞뒤 공백 제거
  3. `GEMINI_API_KEY=your_key` 형식 확인 (등호 앞뒤 공백 없음)

### 오류: "Permission denied"
- **원인**: 
  - API가 활성화되지 않음
  - 프로젝트에 결제 정보가 없음
- **해결**:
  1. Google Cloud Console에서 Generative Language API 활성화
  2. 결제 계정 연결 (무료 할당량 사용 가능)

## 🔒 보안 주의사항

1. **절대 공개하지 마세요**: API 키는 비밀 정보입니다
2. **Git에 커밋 금지**: `.env` 파일은 `.gitignore`에 추가
3. **환경 변수 사용**: 프로덕션에서는 환경 변수로 관리 권장

## 📝 .env 파일 예시

```env
# Gemini API Key
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Database URL (선택사항)
DATABASE_URL=sqlite:///./synk_mvp.db
```

## ✅ 설정 확인

서버 실행 후 다음 메시지가 표시되면 정상입니다:
```
✅ 데이터베이스 초기화 완료
```

다음 경고가 표시되면 API 키를 확인하세요:
```
⚠️ 경고: GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.
```
