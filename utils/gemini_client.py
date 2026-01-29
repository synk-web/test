"""
Gemini API 클라이언트
공통 Gemini API 설정 및 응답 생성 유틸리티
"""
import os
import google.generativeai as genai
from typing import Optional
from fastapi import HTTPException

from utils.config import load_env, get_gemini_api_key


class GeminiClient:
    """Gemini API 클라이언트 싱글톤"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not GeminiClient._initialized:
            # 환경 변수 로드 (최적화 전 방식과 동일)
            # 최적화 전: chat_multi.py에서 직접 load_dotenv 호출
            load_env()
            
            # API 키 설정 (최적화 전 방식과 동일)
            # 최적화 전: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            api_key = get_gemini_api_key()
            
            if api_key:
                # API 키 일부만 로그에 표시 (보안)
                masked_key = f"{api_key[:10]}...{api_key[-5:]}" if len(api_key) > 15 else "***"
                print(f"✅ Gemini API 키 로드됨: {masked_key} (길이: {len(api_key)})")
                
                # 최적화 전 방식과 동일: genai.configure(api_key=GEMINI_API_KEY)
                genai.configure(api_key=api_key)
                self.api_key = api_key
                self.configured = True
            else:
                self.api_key = None
                self.configured = False
                print("⚠️ 경고: GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
            
            GeminiClient._initialized = True
    
    def reload_api_key(self):
        """
        API 키를 다시 로드 (서버 재시작 없이 .env 변경 반영)
        """
        load_env()
        new_api_key = get_gemini_api_key()
        if new_api_key:
            if new_api_key != self.api_key:
                masked_key = f"{new_api_key[:10]}...{new_api_key[-5:]}" if len(new_api_key) > 15 else "***"
                print(f"🔄 Gemini API 키 재로드됨: {masked_key} (길이: {len(new_api_key)})")
                genai.configure(api_key=new_api_key)
                self.api_key = new_api_key
                self.configured = True
                return True
        return False
    
    def generate_response(
        self,
        prompt: str,
        model_name: str = "gemini-2.0-flash"
    ) -> str:
        """
        Gemini API로 응답 생성
        
        Args:
            prompt: 프롬프트
            model_name: 모델 이름
        
        Returns:
            생성된 응답 텍스트
        
        Raises:
            HTTPException: API 키가 없거나 생성 실패 시
        """
        if not self.configured:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY=your_api_key 형식으로 추가해주세요."
            )
        
        try:
            # 모델 이름 정규화
            # Google Generative AI SDK는 "models/" 접두사가 있는 전체 경로를 받습니다
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"
            
            # 안정적인 모델로 변경 (실험 버전 제외)
            if "exp" in model_name.lower() or "preview" in model_name.lower():
                model_name = "models/gemini-2.0-flash"
                print(f"⚠️ 실험 버전 모델 감지, 안정 버전으로 변경: {model_name}")
            
            # 모델명 그대로 사용 (접두사 포함)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            character_response = response.text.strip()
            
            if not character_response:
                raise ValueError("캐릭터 응답이 비어있습니다.")
            
            return character_response
        
        except Exception as e:
            error_detail = str(e)
            
            # 모델을 찾을 수 없는 오류 처리
            if "404" in error_detail or "not found" in error_detail.lower() or "not supported" in error_detail.lower():
                available_models = [
                    "gemini-2.0-flash",
                    "gemini-2.5-flash",
                    "gemini-flash-latest",
                    "gemini-pro-latest"
                ]
                # 실제 사용한 모델명 표시 (접두사 제거된 버전)
                actual_model = model_name if not model_name.startswith("models/") else model_name[7:]
                raise HTTPException(
                    status_code=404,
                    detail=f"모델 '{actual_model}'을 찾을 수 없거나 지원되지 않습니다. 사용 가능한 모델: {', '.join(available_models)}"
                )
            
            # API 키 관련 오류 처리
            if "API_KEY" in error_detail or "api key" in error_detail.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Gemini API 키가 유효하지 않습니다. .env 파일의 GEMINI_API_KEY를 확인해주세요."
                )
            
            # API 키 정지 오류 처리
            if "suspended" in error_detail.lower() or "CONSUMER_SUSPENDED" in error_detail:
                raise HTTPException(
                    status_code=403,
                    detail="Gemini API 키가 정지되었습니다. Google Cloud Console에서 API 키 상태를 확인하거나 새로운 API 키를 발급받아 .env 파일에 설정해주세요."
                )
            
            # 권한 거부 오류 처리
            if "permission denied" in error_detail.lower() or "403" in error_detail:
                raise HTTPException(
                    status_code=403,
                    detail="Gemini API 접근이 거부되었습니다. API 키가 유효한지, API가 활성화되어 있는지 확인해주세요."
                )
            
            # 기타 오류
            raise HTTPException(
                status_code=500,
                detail=f"캐릭터 응답 생성 오류: {error_detail[:200]}"  # 오류 메시지 길이 제한
            )


# 싱글톤 인스턴스
gemini_client = GeminiClient()
