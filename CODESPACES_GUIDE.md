# GitHub Codespaces 사용 가이드

## 🚀 Codespaces에서 실행하기

### 1. Codespaces 생성

1. GitHub 저장소 페이지 (https://github.com/synk-web/test) 접속
2. "Code" 버튼 클릭
3. "Codespaces" 탭 선택
4. "Create codespace on main" 클릭
5. Codespaces가 생성될 때까지 대기 (약 1-2분)

### 2. 환경 변수 설정

Codespaces 터미널에서:

```bash
cp .env.example .env
nano .env  # 또는 원하는 에디터 사용
```

`.env` 파일에 다음을 입력:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPERBASE_URL=https://your-project.supabase.co
SUPERBASE_API_KEY=your_supabase_api_key
SUPERBASE_SECRET_KEY=your_supabase_secret_key
```

### 3. 서버 실행

```bash
python main.py
```

### 4. 포트 포워딩 및 접속

1. Codespaces 하단의 "Ports" 탭 클릭
2. 포트 8000이 자동으로 감지됨
3. 포트 8000 옆의 "Public" 버튼 클릭하여 공개 URL 생성
4. "Open in Browser" 클릭하거나 URL 복사

### 5. 접속 URL

- **채팅 UI**: `https://your-codespace-xxxxx-8000.app.github.dev/`
- **창작자 스튜디오**: `https://your-codespace-xxxxx-8000.app.github.dev/creator.html`
- **API 문서**: `https://your-codespace-xxxxx-8000.app.github.dev/docs`

## 💡 팁

- Codespaces 무료 플랜: 월 60시간 제공
- 포트는 자동으로 포워딩되며, Public으로 설정하면 외부에서도 접근 가능
- `.env` 파일은 Codespaces에만 저장되며, GitHub에는 커밋되지 않습니다
- Codespaces를 중지하면 데이터는 유지되지만, 재시작 시 포트 URL이 변경될 수 있습니다

## 🔒 보안

- Public 포트는 누구나 접근 가능하므로, 테스트용으로만 사용하세요
- 프로덕션 환경에서는 인증을 추가하거나 Private 포트를 사용하세요
