# Google 로그인 설정 가이드

## 🔐 Supabase에서 Google OAuth 설정

### 1. Google Cloud Console 설정

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/ 접속
   - 프로젝트 선택 또는 새 프로젝트 생성

2. **OAuth 동의 화면 설정**
   - 좌측 메뉴: "APIs & Services" → "OAuth consent screen"
   - User Type 선택: "External" (일반 사용자용)
   - 앱 정보 입력:
     - App name: SYNK MVP
     - User support email: 본인 이메일
     - Developer contact: 본인 이메일
   - "Save and Continue" 클릭

3. **OAuth 클라이언트 ID 생성**
   - "APIs & Services" → "Credentials"
   - "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: SYNK MVP
   - Authorized redirect URIs 추가:
     ```
     https://fpffwqcqmnltchnnttic.supabase.co/auth/v1/callback
     ```
   - "Create" 클릭
   - **Client ID**와 **Client Secret** 복사 (나중에 필요)

### 2. Supabase 대시보드 설정

1. **Supabase 대시보드 접속**
   - https://supabase.com/dashboard
   - 프로젝트 선택

2. **Authentication 설정**
   - 좌측 메뉴: "Authentication" → "Providers"
   - "Google" 클릭

3. **Google Provider 활성화**
   - "Enable Google provider" 토글 ON
   - **Client ID (for OAuth)** 입력: Google Cloud Console에서 복사한 Client ID
   - **Client Secret (for OAuth)** 입력: Google Cloud Console에서 복사한 Client Secret
   - "Save" 클릭

4. **Redirect URL 확인**
   - Supabase가 자동으로 생성한 Redirect URL 확인:
     ```
     https://fpffwqcqmnltchnnttic.supabase.co/auth/v1/callback
     ```
   - 이 URL을 Google Cloud Console의 Authorized redirect URIs에 추가했는지 확인

### 3. 테스트

1. **서버 실행**
   ```bash
   python main.py
   ```

2. **브라우저에서 접속**
   - http://localhost:8000/ 또는 http://localhost:8000/creator.html

3. **로그인 테스트**
   - 우측 상단 "Google로 로그인" 버튼 클릭
   - Google 계정 선택
   - 권한 승인
   - 리다이렉트 후 로그인 상태 확인

## ✅ 완료 체크리스트

- [ ] Google Cloud Console에서 OAuth 클라이언트 ID 생성
- [ ] Google Cloud Console에 Supabase Redirect URL 추가
- [ ] Supabase 대시보드에서 Google Provider 활성화
- [ ] Client ID와 Client Secret 입력
- [ ] 로그인 테스트 완료

## 🔒 보안 주의사항

- Client Secret은 절대 공개하지 마세요
- `.env` 파일에 저장하지 마세요 (Supabase 대시보드에만 저장)
- 프로덕션 환경에서는 추가 보안 설정을 고려하세요

## 🐛 문제 해결

### "redirect_uri_mismatch" 오류
- Google Cloud Console의 Authorized redirect URIs에 Supabase URL이 정확히 추가되었는지 확인
- URL 끝에 슬래시(/)가 없어야 함

### "invalid_client" 오류
- Client ID와 Client Secret이 정확한지 확인
- Supabase 대시보드에서 다시 입력

### 로그인 후 리다이렉트가 안 됨
- Supabase 대시보드의 Redirect URL 설정 확인
- 브라우저 콘솔에서 오류 메시지 확인
