"""
SYNK MVP - 메인 애플리케이션
FastAPI 기반 캐릭터 채팅 시스템
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# 라우터 import
from api.character_api import router as character_router
from api.chat_multi import router as chat_multi_router
from api.opening import router as opening_router
from api.reaction import router as reaction_router
from api.user_profile import router as user_profile_router

# 창작자 스튜디오 라우터
from api.auth import router as auth_router
from api.creator_works import router as creator_works_router
from api.creator_characters import router as creator_characters_router
from api.creator_images import router as creator_images_router
from api.creator_lorebook import router as creator_lorebook_router
from api.creator_openings import router as creator_openings_router

# DB 초기화
from db.character_db import init_character_db
from db.database import init_db

# FastAPI 앱 생성
app = FastAPI(
    title="SYNK MVP - 캐릭터 채팅 시스템",
    description="AI 캐릭터와의 대화 시스템",
    version="1.0.0"
)

# CORS 설정 (프론트엔드에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(character_router)
app.include_router(chat_multi_router)
app.include_router(opening_router)
app.include_router(reaction_router)
app.include_router(user_profile_router)

# 창작자 스튜디오 라우터
app.include_router(auth_router)
app.include_router(creator_works_router)
app.include_router(creator_characters_router)
app.include_router(creator_images_router)
app.include_router(creator_lorebook_router)
app.include_router(creator_openings_router)

# 정적 파일 서빙 (UI)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def read_root():
    """루트 경로 - 채팅 UI 반환"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "SYNK MVP - 캐릭터 채팅 시스템", "docs": "/docs"}


@app.get("/creator.html")
async def creator_studio():
    """창작자 스튜디오 UI 반환"""
    creator_path = os.path.join(static_dir, "creator.html")
    if os.path.exists(creator_path):
        return FileResponse(creator_path)
    return {"error": "Creator studio not found"}


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    print("=" * 60)
    print("🚀 SYNK MVP 서버 시작")
    print("=" * 60)
    
    # DB 초기화
    init_db()  # 관계 데이터 DB
    init_character_db()  # 캐릭터 DB
    
    print("✅ 데이터베이스 초기화 완료")
    print("=" * 60)
    print("📝 API 문서: http://localhost:8000/docs")
    print("💬 채팅 UI: http://localhost:8000/")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
