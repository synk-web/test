"""
SYNK MVP 통합 테스트 스크립트
=============================
실제 API를 호출하여 전체 플로우를 테스트합니다.

사용법:
1. 서버 실행: python main.py
2. 테스트 실행: python synk_integration_test.py
"""

import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# 테스트용 데이터
TEST_USER_ID = "test_user_001"
TEST_CHARACTER_ID = "lee_gaeun"  # 이가은
CHARACTER_NAME = "이가은"
CHARACTER_PERSONALITY = """
17세 여고생, 츤데레 성격.
말투: 반말, 짧은 문장, "...뭐야", "흥", "시끄러워"
비밀: 그림 그리기 (들키면 당황)
유저와는 소꿉친구 관계
"""


async def test_chat(client: httpx.AsyncClient, message: str) -> dict:
    """채팅 API 테스트"""
    response = await client.post(
        f"{BASE_URL}/api/chat/",
        json={
            "user_id": TEST_USER_ID,
            "character_id": TEST_CHARACTER_ID,
            "message": message,
            "character_name": CHARACTER_NAME,
            "character_personality": CHARACTER_PERSONALITY
        }
    )
    return response.json()


async def test_reaction(client: httpx.AsyncClient, turn_id: str, emoji: str, 
                        user_message: str = "", character_response: str = "") -> dict:
    """이모지 리액션 API 테스트"""
    response = await client.post(
        f"{BASE_URL}/api/reaction/",
        json={
            "user_id": TEST_USER_ID,
            "character_id": TEST_CHARACTER_ID,
            "turn_id": turn_id,
            "emoji": emoji,
            "user_message": user_message,
            "character_response": character_response
        }
    )
    return response.json()


async def get_relationship(client: httpx.AsyncClient) -> dict:
    """관계 데이터 조회"""
    response = await client.get(
        f"{BASE_URL}/api/reaction/relationship/{TEST_USER_ID}/{TEST_CHARACTER_ID}"
    )
    return response.json()


async def run_test_scenario():
    """
    테스트 시나리오 실행
    
    시나리오:
    1. 첫 인사 → 캐릭터 반응 확인
    2. ❤️ 리액션 → intimacy 증가 확인
    3. 도발적 대화 → 캐릭터 반응 확인
    4. 💢 리액션 → anger_peaks 증가 확인
    5. 특별한 순간 → ⭐ 리액션 → 핵심 기억 저장 확인
    6. 명령형 대화 → dominance 변화 확인
    7. 최종 관계 데이터 확인
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("🧪 SYNK MVP 통합 테스트 시작")
        print("=" * 60)
        print(f"유저: {TEST_USER_ID}")
        print(f"캐릭터: {CHARACTER_NAME}")
        print("=" * 60)
        
        # ═══════════════════════════════════════
        # 테스트 1: 첫 인사
        # ═══════════════════════════════════════
        print("\n📝 테스트 1: 첫 인사")
        print("-" * 40)
        
        result = await test_chat(client, "안녕 가은아")
        turn_id_1 = result.get("turn_id", "")
        response_1 = result.get("character_response", "")
        
        print(f"유저: 안녕 가은아")
        print(f"이가은: {response_1[:100]}...")
        print(f"Turn ID: {turn_id_1}")
        
        # ❤️ 리액션
        print("\n→ ❤️ 리액션 추가")
        reaction_result = await test_reaction(
            client, turn_id_1, "❤️",
            user_message="안녕 가은아",
            character_response=response_1
        )
        print(f"결과: {reaction_result.get('message', '')}")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 테스트 2: 일상 대화
        # ═══════════════════════════════════════
        print("\n📝 테스트 2: 일상 대화")
        print("-" * 40)
        
        result = await test_chat(client, "오늘 뭐해?")
        turn_id_2 = result.get("turn_id", "")
        response_2 = result.get("character_response", "")
        
        print(f"유저: 오늘 뭐해?")
        print(f"이가은: {response_2[:100]}...")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 테스트 3: 비밀 관련 대화 (그림)
        # ═══════════════════════════════════════
        print("\n📝 테스트 3: 비밀 관련 대화")
        print("-" * 40)
        
        result = await test_chat(client, "너 혹시 그림 그려?")
        turn_id_3 = result.get("turn_id", "")
        response_3 = result.get("character_response", "")
        
        print(f"유저: 너 혹시 그림 그려?")
        print(f"이가은: {response_3[:100]}...")
        
        # ⭐ 핵심 기억으로 저장
        print("\n→ ⭐ 핵심 기억 저장")
        reaction_result = await test_reaction(
            client, turn_id_3, "⭐",
            user_message="너 혹시 그림 그려?",
            character_response=response_3
        )
        print(f"결과: {reaction_result.get('message', '')}")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 테스트 4: 도발적 대화
        # ═══════════════════════════════════════
        print("\n📝 테스트 4: 도발적 대화")
        print("-" * 40)
        
        result = await test_chat(client, "야 바보야 ㅋㅋ")
        turn_id_4 = result.get("turn_id", "")
        response_4 = result.get("character_response", "")
        
        print(f"유저: 야 바보야 ㅋㅋ")
        print(f"이가은: {response_4[:100]}...")
        
        # 💢 리액션 (트리거 키워드 테스트)
        print("\n→ 💢 리액션 추가")
        reaction_result = await test_reaction(
            client, turn_id_4, "💢",
            user_message="야 바보야 ㅋㅋ",
            character_response=response_4
        )
        print(f"결과: {reaction_result.get('message', '')}")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 테스트 5: 명령형 대화 (Dominance 테스트)
        # ═══════════════════════════════════════
        print("\n📝 테스트 5: 명령형 대화 (Dominance)")
        print("-" * 40)
        
        result = await test_chat(client, "이거 해줘")
        turn_id_5 = result.get("turn_id", "")
        response_5 = result.get("character_response", "")
        
        print(f"유저: 이거 해줘")
        print(f"이가은: {response_5[:100]}...")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 테스트 6: 사과 (Dominance 반전)
        # ═══════════════════════════════════════
        print("\n📝 테스트 6: 사과 (Dominance)")
        print("-" * 40)
        
        result = await test_chat(client, "미안해, 잘못했어")
        turn_id_6 = result.get("turn_id", "")
        response_6 = result.get("character_response", "")
        
        print(f"유저: 미안해, 잘못했어")
        print(f"이가은: {response_6[:100]}...")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 테스트 7: 열광 반응 테스트
        # ═══════════════════════════════════════
        print("\n📝 테스트 7: 열광 반응")
        print("-" * 40)
        
        result = await test_chat(client, "너 진짜 대단하다!")
        turn_id_7 = result.get("turn_id", "")
        response_7 = result.get("character_response", "")
        
        print(f"유저: 너 진짜 대단하다!")
        print(f"이가은: {response_7[:100]}...")
        
        # 🔥 리액션
        print("\n→ 🔥 리액션 추가")
        reaction_result = await test_reaction(
            client, turn_id_7, "🔥",
            user_message="너 진짜 대단하다!",
            character_response=response_7
        )
        print(f"결과: {reaction_result.get('message', '')}")
        
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════
        # 최종: 관계 데이터 확인
        # ═══════════════════════════════════════
        print("\n" + "=" * 60)
        print("📊 최종 관계 데이터")
        print("=" * 60)
        
        try:
            rel_data = await get_relationship(client)
            
            print(f"""
유저 ID: {rel_data.get('user_id', 'N/A')}
캐릭터 ID: {rel_data.get('character_id', 'N/A')}

📈 감정 통계:
  - 기쁨 피크: {rel_data.get('emotional_stats', {}).get('joy_peaks', 0)}회
  - 화남 피크: {rel_data.get('emotional_stats', {}).get('anger_peaks', 0)}회
  - 열광 피크: {rel_data.get('emotional_stats', {}).get('excitement_peaks', 0)}회

💕 친밀도: {rel_data.get('intimacy', 0):.1f}/10.0

⚖️ 관계 주도권 (Dominance):
  - 점수: {rel_data.get('dominance', {}).get('score', 0):.2f}
  - 히스토리: {len(rel_data.get('dominance', {}).get('history', []))}개

⭐ 핵심 기억: {len(rel_data.get('core_memories', []))}개
""")
            
            # 핵심 기억 상세
            if rel_data.get('core_memories'):
                print("핵심 기억 목록:")
                for i, mem in enumerate(rel_data.get('core_memories', [])[:3], 1):
                    print(f"  {i}. {mem.get('summary', 'N/A')}")
                    print(f"     트리거 키워드: {mem.get('trigger_keywords', [])}")
            
            # 트리거 키워드
            if rel_data.get('trigger_keywords'):
                print(f"\n🔥 트리거 키워드:")
                for t in rel_data.get('trigger_keywords', []):
                    print(f"  - {t.get('keyword', 'N/A')} ({t.get('emotion', 'N/A')}, {t.get('occurrence_count', 0)}회)")
            
            print(f"\n감정 로그 수: {rel_data.get('emotion_log_count', 0)}개")
            
        except Exception as e:
            print(f"관계 데이터 조회 실패: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 통합 테스트 완료!")
        print("=" * 60)


async def run_dominance_test():
    """
    Dominance 변화 집중 테스트
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("⚖️ Dominance 변화 집중 테스트")
        print("=" * 60)
        
        # 초기 상태
        print("\n[초기 상태]")
        try:
            rel_data = await get_relationship(client)
            print(f"Dominance: {rel_data.get('dominance', {}).get('score', 0):.3f}")
        except:
            print("관계 데이터 없음 (새로 생성됨)")
        
        # 유저 우위 패턴 (명령)
        commands = ["이거 해줘", "빨리 해", "말해봐", "보여줘"]
        print(f"\n[유저 명령 패턴 테스트] ({len(commands)}개)")
        
        for cmd in commands:
            result = await test_chat(client, cmd)
            print(f"  유저: {cmd}")
            print(f"  캐릭터: {result.get('character_response', '')[:50]}...")
            await asyncio.sleep(0.5)
        
        rel_data = await get_relationship(client)
        print(f"\n→ 현재 Dominance: {rel_data.get('dominance', {}).get('score', 0):.3f}")
        
        # 유저 순응 패턴 (사과)
        apologies = ["미안해", "죄송해", "잘못했어", "내가 나빴어"]
        print(f"\n[유저 순응 패턴 테스트] ({len(apologies)}개)")
        
        for apology in apologies:
            result = await test_chat(client, apology)
            print(f"  유저: {apology}")
            print(f"  캐릭터: {result.get('character_response', '')[:50]}...")
            await asyncio.sleep(0.5)
        
        rel_data = await get_relationship(client)
        print(f"\n→ 현재 Dominance: {rel_data.get('dominance', {}).get('score', 0):.3f}")
        
        print("\n" + "=" * 60)
        print("✅ Dominance 테스트 완료!")
        print("=" * 60)


async def run_trigger_test():
    """
    트리거 키워드 감지 집중 테스트
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("🔥 트리거 키워드 감지 테스트")
        print("=" * 60)
        
        # 같은 키워드로 여러 번 💢 리액션
        test_keyword = "오이"
        
        for i in range(3):
            print(f"\n[테스트 {i+1}/3]")
            
            result = await test_chat(client, f"{test_keyword} 좋아해?")
            turn_id = result.get("turn_id", "")
            response = result.get("character_response", "")
            
            print(f"유저: {test_keyword} 좋아해?")
            print(f"캐릭터: {response[:50]}...")
            
            # 💢 리액션
            await test_reaction(
                client, turn_id, "💢",
                user_message=f"{test_keyword} 좋아해?",
                character_response=response
            )
            print("→ 💢 리액션 추가")
            
            await asyncio.sleep(0.5)
        
        # 트리거 키워드 확인
        print("\n[트리거 키워드 확인]")
        rel_data = await get_relationship(client)
        
        triggers = rel_data.get('trigger_keywords', [])
        if triggers:
            for t in triggers:
                print(f"  ✅ '{t.get('keyword')}' - {t.get('emotion')} ({t.get('occurrence_count')}회, 신뢰도: {t.get('confidence', 0):.1f})")
        else:
            print("  ⚠️ 확정된 트리거 키워드 없음")
        
        print("\n" + "=" * 60)
        print("✅ 트리거 키워드 테스트 완료!")
        print("=" * 60)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          SYNK MVP 통합 테스트 스크립트                      ║
╠════════════════════════════════════════════════════════════╣
║  1. 전체 시나리오 테스트                                    ║
║  2. Dominance 집중 테스트                                   ║
║  3. 트리거 키워드 집중 테스트                               ║
║  4. 전체 테스트 (1+2+3)                                     ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("테스트 선택 (1-4, 기본값: 1): ").strip() or "1"
    
    if choice == "1":
        asyncio.run(run_test_scenario())
    elif choice == "2":
        asyncio.run(run_dominance_test())
    elif choice == "3":
        asyncio.run(run_trigger_test())
    elif choice == "4":
        asyncio.run(run_test_scenario())
        print("\n" + "=" * 60 + "\n")
        asyncio.run(run_dominance_test())
        print("\n" + "=" * 60 + "\n")
        asyncio.run(run_trigger_test())
    else:
        print("잘못된 선택입니다.")
