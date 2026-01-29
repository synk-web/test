"""
Supabase 연결 테스트 스크립트
"""
import sys
from utils.supabase_client import get_supabase_client, get_supabase_admin_client
from utils.config import load_env

def test_supabase_connection():
    """Supabase 연결 테스트"""
    print("=" * 60)
    print("🔌 Supabase 연결 테스트 시작")
    print("=" * 60)
    
    # 환경 변수 로드
    load_env()
    
    # 환경 변수 확인
    import os
    print("\n0️⃣ 환경 변수 확인...")
    supabase_url = os.getenv("SUPERBASE_URL")
    supabase_key = os.getenv("SUPERBASE_API_KEY")
    supabase_secret = os.getenv("SUPERBASE_SECRET_KEY")
    
    if supabase_url:
        # URL의 일부만 표시 (보안)
        url_display = supabase_url[:30] + "..." if len(supabase_url) > 30 else supabase_url
        print(f"   ✅ SUPERBASE_URL: {url_display}")
    else:
        print("   ❌ SUPERBASE_URL: 설정되지 않음")
    
    if supabase_key:
        key_display = supabase_key[:10] + "..." if len(supabase_key) > 10 else supabase_key
        print(f"   ✅ SUPERBASE_API_KEY: {key_display}... (길이: {len(supabase_key)})")
    else:
        print("   ❌ SUPERBASE_API_KEY: 설정되지 않음")
    
    if supabase_secret:
        secret_display = supabase_secret[:10] + "..." if len(supabase_secret) > 10 else supabase_secret
        print(f"   ✅ SUPERBASE_SECRET_KEY: {secret_display}... (길이: {len(supabase_secret)})")
    else:
        print("   ⚠️ SUPERBASE_SECRET_KEY: 설정되지 않음 (선택사항)")
    
    if not supabase_url or not supabase_key:
        print("\n💡 .env 파일에 다음을 추가하세요:")
        print("   SUPERBASE_URL=https://your-project-id.supabase.co")
        print("   SUPERBASE_API_KEY=your_anon_public_key")
        print("   SUPERBASE_SECRET_KEY=your_service_role_key (선택사항)")
        print("\n   Supabase 대시보드 → Settings → API에서 확인할 수 있습니다.")
        return False
    
    # 1. 일반 클라이언트 테스트
    print("\n1️⃣ 일반 클라이언트 연결 테스트...")
    try:
        client = get_supabase_client()
        print("✅ 일반 클라이언트 연결 성공!")
        
        # 간단한 쿼리 테스트 (works 테이블 조회)
        try:
            result = client.table("works").select("work_id").limit(1).execute()
            print(f"✅ 테이블 조회 성공: {len(result.data)}개 결과")
        except Exception as e:
            print(f"⚠️ 테이블 조회 실패 (테이블이 비어있을 수 있음): {e}")
            
    except ValueError as e:
        print(f"❌ 일반 클라이언트 연결 실패: {e}")
        print("\n💡 해결 방법:")
        print("   .env 파일에 다음을 추가하세요:")
        print("   SUPERBASE_URL=https://your-project.supabase.co")
        print("   SUPERBASE_API_KEY=your_anon_public_key")
        return False
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return False
    
    # 2. Admin 클라이언트 테스트
    print("\n2️⃣ Admin 클라이언트 연결 테스트...")
    try:
        admin_client = get_supabase_admin_client()
        print("✅ Admin 클라이언트 연결 성공!")
        
        # Admin 권한이 필요한 작업 테스트
        try:
            result = admin_client.table("works").select("work_id").limit(1).execute()
            print(f"✅ Admin 테이블 조회 성공: {len(result.data)}개 결과")
        except Exception as e:
            print(f"⚠️ Admin 테이블 조회 실패: {e}")
            
    except ValueError as e:
        print(f"⚠️ Admin 클라이언트 연결 실패 (선택사항): {e}")
        print("   Admin 클라이언트는 서비스 역할 키가 필요합니다.")
    except Exception as e:
        print(f"⚠️ Admin 클라이언트 오류: {e}")
    
    # 3. 테이블 존재 확인
    print("\n3️⃣ 테이블 존재 확인...")
    tables_to_check = [
        "works",
        "characters",
        "gallery_images",
        "lorebook_entries",
        "openings",
        "locations",
        "legacy_characters",
        "relationships",
        "user_profiles",
        "story_summaries"
    ]
    
    try:
        client = get_supabase_client()
        for table in tables_to_check:
            try:
                result = client.table(table).select("*").limit(0).execute()
                print(f"   ✅ {table} 테이블 존재")
            except Exception as e:
                if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                    print(f"   ❌ {table} 테이블 없음 (SQL 스크립트 실행 필요)")
                else:
                    print(f"   ⚠️ {table} 테이블 확인 실패: {e}")
    except Exception as e:
        print(f"   ❌ 테이블 확인 중 오류: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 연결 테스트 완료!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
