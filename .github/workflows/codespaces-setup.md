# GitHub Codespaces 사용 가이드

## 🚀 Codespaces에서 실행하기

1. **Codespaces 생성**
   - GitHub 저장소 페이지에서 "Code" 버튼 클릭
   - "Codespaces" 탭 선택
   - "Create codespace on main" 클릭

2. **환경 변수 설정**
   - Codespaces 터미널에서 `.env` 파일 생성:
   ```bash
   cp .env.example .env
   nano .env  # 또는 원하는 에디터 사용
   ```
   - API 키 입력

3. **서버 실행**
   ```bash
   python main.py
   ```

4. **포트 포워딩**
   - Codespaces가 자동으로 포트 8000을 포워딩합니다
   - "Ports" 탭에서 "Public"으로 변경하면 공개 URL 생성
   - 또는 "Ports" 탭에서 "Open in Browser" 클릭

5. **접속**
   - 채팅 UI: `https://your-codespace-url.app.github.dev/`
   - 창작자 스튜디오: `https://your-codespace-url.app.github.dev/creator.html`

## 💡 팁

- Codespaces는 무료 플랜에서 월 60시간 제공
- 포트는 자동으로 포워딩되며, Public으로 설정하면 외부에서도 접근 가능
- `.env` 파일은 Codespaces에만 저장되며, GitHub에는 커밋되지 않습니다
