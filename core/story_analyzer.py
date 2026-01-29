"""
스토리 분석기 - 대화 내용을 AI로 분석하여 요약 생성
"""
from typing import List, Dict, Optional
from utils.gemini_client import gemini_client


async def generate_story_summary(
    user_message: str,
    character_responses: List[Dict],
    character_states: Dict,
    recent_summaries: List[Dict] = None
) -> tuple[str, str]:
    """
    AI로 스토리 요약 및 분석 생성
    
    Returns:
        (ai_summary, ai_analysis) 튜플
        - ai_summary: 간단한 요약 (1-2문장)
        - ai_analysis: 상세 분석 (상황 묘사)
    """
    
    # 캐릭터 응답 상세 정보 구성 (행동 + 대사 + 속마음)
    responses_detail = []
    for r in character_responses:
        char_name = r['character_name']
        action = r.get('action', '').strip()
        message = r.get('message', '').strip()
        inner_thought = r.get('inner_thought', '')
        
        response_info = f"{char_name}"
        if action:
            response_info += f" {action}"
        response_info += f": {message}"
        
        if inner_thought:
            response_info += f"\n  💭 속마음: {inner_thought}"
        
        responses_detail.append(response_info)
    
    responses_text = "\n".join([f"- {r}" for r in responses_detail])
    
    # 캐릭터 상태 정보 (응답하지 않은 캐릭터들)
    states_detail = []
    for char_id, state in character_states.items():
        char_name = state.get('character_name', 'Unknown')
        attention = state.get('attention', 'unknown')
        mood = state.get('current_mood', 'neutral')
        inner_thought = state.get('inner_thought')
        recent = state.get('recent', False)
        
        # 응답하지 않은 캐릭터만 표시
        if not recent:
            state_info = f"{char_name} [상태: {attention}, 기분: {mood}]"
            if inner_thought:
                if isinstance(inner_thought, dict):
                    thought_text = inner_thought.get('thought', '')
                else:
                    thought_text = str(inner_thought)
                if thought_text:
                    state_info += f"\n  💭 속마음: {thought_text}"
            
            states_detail.append(state_info)
    
    states_text = "\n".join([f"- {s}" for s in states_detail]) if states_detail else "없음"
    
    # 최근 요약 컨텍스트
    context_text = ""
    if recent_summaries:
        context_text = "\n[최근 스토리 흐름]\n"
        for summary in recent_summaries[-5:]:  # 최근 5개
            context_text += f"- {summary['ai_summary']}\n"
    
    prompt = f"""
당신은 소설이나 드라마의 시나리오 작가처럼, 대화 상황을 생생하게 묘사하는 스토리 분석가입니다.

[현재 대화 상황]
유저: "{user_message}"

[캐릭터들의 행동과 대사]
{responses_text}

[주변 캐릭터들의 상태와 속마음]
{states_text}
{context_text}

[⚠️ 매우 중요한 지시사항 - 반드시 준수하세요!]
1. **행동, 대사, 상황을 모두 포함하여 생생하게 묘사하세요**
   - 캐릭터가 무엇을 했는지 (행동: 웃었다, 반발했다, 위협했다)
   - 캐릭터가 무엇을 말했는지 (대사: 중요한 대사는 자연스럽게 포함)
   - 어떤 상황이 벌어졌는지 (사건: 충돌, 대립, 관찰)
   - 분위기와 긴장도
   - 행동과 대사를 자연스럽게 조합하여 묘사하세요

2. **속마음을 활용하되 자연스럽게 통합하세요**
   - 속마음을 그대로 옮기지 말고, 캐릭터의 내면 심리로 묘사
   - 예: "속마음: '씨X, 진짜 아프잖아!'" ❌ 절대 금지!
   - 예: "주창윤은 고통을 참으며 강한 척했다" ✅ 올바른 예시

3. **응답 형식 준수**
   - ai_summary와 ai_analysis 모두 행동, 대사, 상황을 포함하여 묘사
   - 대사는 자연스럽게 포함하되, 과도하게 인용하지 마세요

[요청]
1. **간단한 요약 (ai_summary)**: 2-3문장으로 이번 턴의 핵심 사건을 상세하게 요약하세요.
   - 행동 중심: "누가 무엇을 했는지" 구체적으로 묘사
   - 대사 포함: 중요한 대사는 자연스럽게 포함
   - 사건 중심: "어떤 상황이 벌어졌는지" 명확하게 설명
   - 캐릭터 간 상호작용: 누가 누구에게 어떻게 반응했는지
   - ✅ 올바른 예시: "유저가 주창윤의 팔목을 강하게 잡으며 위협적인 자세를 취했고, 주창윤은 당황하며 손을 뿌리치려고 시도했다. 주창윤은 분노한 표정으로 유저를 노려보며 '야, 손 안 놔? 지금 나 협박하는 거야?'라고 반발했고, 황인하가 옆에서 차갑게 관찰하며 '후후... 재미있네'라고 말했다. 표다은은 걱정스러운 표정으로 상황을 지켜보며 개입을 망설이고 있었고, 고선하는 경멸적인 시선으로 한쪽에서 상황을 관찰했다."

2. **상세 분석 (ai_analysis)**: 상황을 소설처럼 생생하고 디테일하게 묘사하세요 (5-8문장).
   - 캐릭터들의 구체적인 행동, 표정, 몸짓, 시선
   - 캐릭터들의 중요한 대사를 자연스럽게 포함
   - 분위기와 긴장도를 생생하게 묘사
   - 캐릭터들의 내면 심리를 깊이 있게 묘사 (속마음을 바탕으로 추론하되, 속마음을 그대로 옮기지 말고 심리 상태로 묘사)
   - 캐릭터 간의 미묘한 상호작용과 관계 역학
   - 중요한 사건이나 관계 변화를 구체적으로 설명
   - 공간감과 시간감을 느낄 수 있도록 묘사
   - ✅ 올바른 예시: "베타 동 로비에 날카로운 긴장감이 공기를 가르며 퍼져나갔다. 유저가 주창윤의 팔목을 강하게 잡는 물리적 위협에 주창윤은 눈을 부릅뜨며 당황한 표정을 지었지만, 곧바로 분노로 변한 얼굴로 유저를 노려보며 '야, 손 안 놔? 지금 나 협박하는 거야?'라고 반발하며 손을 뿌리치려고 시도했다. 주창윤의 속마음에는 두려움이 섞여 있었지만, 강한 척하며 맞서려는 의지가 엿보였다. 황인하는 한쪽 구석에 기대어 나른한 눈빛으로 차갑게 관찰하며 이 상황을 흥미롭게 지켜보고 있었고, 입꼬리를 살짝 올리며 '후후... 재미있네. 얼마나 버틸 수 있을까?'라고 냉소적인 미소를 지었다. 표다은은 걱정스러운 표정으로 상황을 지켜보며 입을 벌렸다가 다시 닫는 등 개입을 망설이고 있었고, 손가락을 꼬며 불안해하는 모습이었다. 고선하는 손수건으로 입가를 닦으며 경멸적인 시선으로 한쪽에서 상황을 관찰하고 있었고, '어머, 시끄러워'라고 중얼거리며 이 모든 상황이 자신의 품격을 떨어뜨리는 것처럼 보였다는 표정을 지었다." 

[응답 형식 - 반드시 준수하세요]
ai_summary: [간단한 요약 - 행동, 대사, 사건 중심, 2-3문장, 구체적이고 디테일하게]
ai_analysis: [상세 분석 - 소설처럼 생생한 묘사, 행동과 대사 포함, 5-8문장, 매우 디테일하고 구체적으로]

⚠️ 최종 확인:
- 행동, 대사, 상황을 모두 포함하여 생생하게 묘사하세요!
- 중요한 대사는 자연스럽게 포함하되, 과도하게 인용하지 마세요!
- 구체적인 행동, 표정, 몸짓, 시선, 분위기를 상세하게 묘사하세요!
- 캐릭터들의 내면 심리와 관계 역학을 깊이 있게 묘사하세요!
- 대사는 따옴표 없이 자연스럽게 문장에 포함시키세요!
"""
    
    try:
        response = gemini_client.generate_response(prompt)
        
        # 응답 파싱
        lines = response.strip().split("\n")
        ai_summary = ""
        ai_analysis = ""
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("ai_summary:"):
                current_section = "summary"
                ai_summary = line.replace("ai_summary:", "").strip()
            elif line.startswith("ai_analysis:"):
                current_section = "analysis"
                ai_analysis = line.replace("ai_analysis:", "").strip()
            elif current_section == "summary" and line and not line.startswith("ai_"):
                ai_summary += " " + line
            elif current_section == "analysis" and line and not line.startswith("ai_"):
                ai_analysis += " " + line
        
        # 대사 정리 함수 (과도한 따옴표나 인용부호만 정리, 대사 내용은 유지)
        def clean_formatting(text):
            """과도한 따옴표나 형식만 정리, 대사 내용은 유지"""
            import re
            if not text:
                return text
            
            # 연속된 공백 정리
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
        
        # 파싱 실패 시 기본값
        if not ai_summary:
            ai_summary = response[:100] + "..."
        if not ai_analysis:
            ai_analysis = response
        
        # 형식만 정리 (대사는 유지)
        ai_summary = clean_formatting(ai_summary)
        ai_analysis = clean_formatting(ai_analysis)
        
        # 빈 문자열 체크
        if not ai_summary or len(ai_summary) < 10:
            ai_summary = response[:100].replace('"', '').replace("'", "") + "..."
        if not ai_analysis or len(ai_analysis) < 10:
            ai_analysis = response.replace('"', '').replace("'", "")
        
        return ai_summary.strip(), ai_analysis.strip()
    except Exception as e:
        print(f"⚠️ 스토리 요약 생성 오류: {e}")
        # 기본 요약 반환
        summary = f"유저: '{user_message[:50]}...' → {len(character_responses)}명 응답"
        analysis = f"이번 턴에서 {len(character_responses)}명의 캐릭터가 응답했습니다."
        return summary, analysis


def build_story_context_for_prompt(recent_summaries: List[Dict]) -> str:
    """
    프롬프트에 포함할 스토리 컨텍스트 생성
    
    Args:
        recent_summaries: 최근 스토리 요약 리스트
    
    Returns:
        프롬프트에 포함할 문자열
    """
    if not recent_summaries:
        return ""
    
    context_lines = [
        "═══════════════════════════════════════",
        "[📖 최근 스토리 흐름 - 반드시 참고하세요]",
        "═══════════════════════════════════════",
        "",
        "이전 대화에서 일어난 중요한 사건들입니다. 이 정보를 바탕으로 일관성 있게 응답하세요.",
        ""
    ]
    
    # 최근 10턴의 요약과 분석 포함
    for i, summary in enumerate(recent_summaries[-10:], 1):
        turn_num = summary.get('turn_number', i)
        context_lines.append(f"[턴 {turn_num}]")
        context_lines.append(f"요약: {summary.get('ai_summary', '')}")
        if summary.get('ai_analysis'):
            analysis = summary['ai_analysis']
            # 분석이 너무 길면 요약
            if len(analysis) > 200:
                analysis = analysis[:200] + "..."
            context_lines.append(f"상황: {analysis}")
        context_lines.append("")
    
    context_lines.append("═══════════════════════════════════════")
    
    return "\n".join(context_lines)
