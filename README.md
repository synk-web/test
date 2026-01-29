# SYNK MVP - AI 캐릭터 챗 시스템

AI 캐릭터와의 대화 시스템 및 창작자 스튜디오

## 🚀 기능

### 채팅 시스템
- 멀티 캐릭터 대화
- 오프닝 시나리오 선택
- 이모지 리액션
- Scene Dashboard (맥락 유지)
- 연쇄 반응 시스템

### 창작자 스튜디오
- 작품 생성 및 관리
- 캐릭터 설정 (AI 자동 생성 지원)
- 이미지 갤러리
- 로어북 관리
- 오프닝 설정

## 📋 요구사항

- Python 3.8+
- Supabase 계정
- Gemini API 키

## 🛠️ 설치 및 실행

### 방법 1: GitHub Codespaces (추천 - 웹에서 바로 실행)

1. **Codespaces 생성**
   - 저장소 페이지에서 "Code" → "Codespaces" → "Create codespace on main"
   - 또는: https://github.com/codespaces/new?repo=synk-web/test

2. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일 편집하여 API 키 입력
   ```

3. **서버 실행**
   ```bash
   python main.py
   ```

4. **포트 포워딩**
   - Codespaces가 자동으로 포트 8000을 포워딩
   - "Ports" 탭에서 "Public"으로 변경하면 공개 URL 생성
   - "Open in Browser" 클릭하여 접속

### 방법 2: 로컬 실행

#### 1. 저장소 클론

```bash
git clone https://github.com/synk-web/test.git
cd test
```

#### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

#### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음을 추가하세요:

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Supabase
SUPERBASE_URL=https://your-project.supabase.co
SUPERBASE_API_KEY=your_supabase_api_key
SUPERBASE_SECRET_KEY=your_supabase_secret_key
```

**⚠️ 중요**: `.env` 파일은 절대 GitHub에 커밋하지 마세요!

#### 4. Supabase 데이터베이스 설정

1. Supabase 대시보드 접속: https://supabase.com/dashboard
2. 새 프로젝트 생성
3. SQL Editor에서 `supabase_schema.sql` 파일의 내용 실행

#### 5. 서버 실행

```bash
python main.py
```

서버가 실행되면:
- 채팅 UI: http://localhost:8000/
- 창작자 스튜디오: http://localhost:8000/creator.html
- API 문서: http://localhost:8000/docs

## 📁 프로젝트 구조

```
v0/
├── api/                    # API 엔드포인트
│   ├── chat_multi.py       # 멀티 캐릭터 채팅
│   ├── creator_works.py    # 작품 CRUD
│   ├── creator_characters.py # 캐릭터 CRUD
│   └── ...
├── core/                   # 핵심 로직
│   ├── scene_manager.py    # Scene Context 관리
│   ├── speaker_selector.py # 화자 선택
│   └── ...
├── db/                     # 데이터베이스
│   └── supabase_db.py      # Supabase 연동
├── models/                 # 데이터 모델
├── static/                 # 프론트엔드
│   ├── index.html          # 채팅 UI
│   └── creator.html        # 창작자 스튜디오
├── utils/                  # 유틸리티
│   ├── config.py           # 환경 설정
│   ├── gemini_client.py    # Gemini API 클라이언트
│   └── supabase_client.py  # Supabase 클라이언트
├── main.py                 # 메인 애플리케이션
├── requirements.txt        # Python 의존성
└── supabase_schema.sql     # Supabase 스키마
```

## 🔐 보안 주의사항

- `.env` 파일은 절대 커밋하지 마세요
- API 키는 환경 변수로 관리하세요
- 프로덕션에서는 CORS 설정을 제한하세요

## 📝 API 문서

서버 실행 후 http://localhost:8000/docs 에서 자동 생성된 API 문서를 확인할 수 있습니다.

## 🤝 기여

이슈나 Pull Request를 환영합니다!

## 📄 라이선스

[라이선스 정보]
