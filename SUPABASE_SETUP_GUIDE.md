# Supabase 설정 가이드

## 📋 SQL 스키마 실행 방법

1. **Supabase 대시보드 접속**
   - https://supabase.com/dashboard 접속
   - 프로젝트 선택

2. **SQL Editor 열기**
   - 왼쪽 메뉴에서 "SQL Editor" 클릭
   - "New query" 클릭

3. **SQL 스키마 실행**
   - `supabase_schema.sql` 파일의 내용을 복사
   - SQL Editor에 붙여넣기
   - "Run" 버튼 클릭

4. **확인 사항**
   - 모든 테이블이 생성되었는지 확인 (Table Editor에서 확인)
   - RLS 정책이 활성화되었는지 확인
   - 인덱스가 생성되었는지 확인

## 🔑 환경 변수 설정

`.env` 파일에 다음을 추가하세요:

```env
# Supabase 설정 (사용자가 SUPERBASE로 오타했지만 그대로 사용)
SUPERBASE_URL=https://your-project.supabase.co
SUPERBASE_API_KEY=your-anon-key
SUPERBASE_SECRET_KEY=your-service-role-key
```

### Supabase 키 찾는 방법

1. **Supabase 대시보드** → **Settings** → **API**
2. **Project URL**: `SUPERBASE_URL`에 사용
3. **anon public key**: `SUPERBASE_API_KEY`에 사용
4. **service_role secret key**: `SUPERBASE_SECRET_KEY`에 사용

## 🔐 구글 로그인 설정

### Supabase에서 구글 OAuth 설정

1. **Supabase 대시보드** → **Authentication** → **Providers**
2. **Google** 클릭
3. **Enable Google provider** 체크
4. **Client ID**와 **Client Secret** 입력 (Google Cloud Console에서 발급)
5. **Redirect URL** 설정: `https://your-project.supabase.co/auth/v1/callback`

### Google Cloud Console 설정

1. **Google Cloud Console** 접속
2. **APIs & Services** → **Credentials**
3. **OAuth 2.0 Client ID** 생성
4. **Authorized redirect URIs**에 Supabase 콜백 URL 추가:
   - `https://your-project.supabase.co/auth/v1/callback`

## 📝 생성된 테이블

다음 테이블들이 생성됩니다:

1. **works** - 작품 정보
2. **characters** - 캐릭터 정보
3. **gallery_images** - 이미지 갤러리
4. **lorebook_entries** - 로어북 항목
5. **openings** - 오프닝 설정

## 🔒 Row Level Security (RLS)

모든 테이블에 RLS가 활성화되어 있습니다:

- **작품 소유자**: 자신의 작품을 완전히 관리 가능
- **공개 작품**: 모든 사용자가 조회 가능
- **비공개 작품**: 소유자만 접근 가능
- **링크 공유 작품**: 모든 사용자가 조회 가능 (unlisted)

## ✅ 확인 체크리스트

- [ ] SQL 스키마 실행 완료
- [ ] 모든 테이블 생성 확인
- [ ] RLS 정책 활성화 확인
- [ ] 환경 변수 설정 완료
- [ ] 구글 OAuth 설정 완료 (선택)
- [ ] API 테스트 완료

## 🚀 다음 단계

1. SQL 스키마 실행 후 이 파일을 알려주세요
2. 환경 변수 설정 확인
3. API 테스트 진행
