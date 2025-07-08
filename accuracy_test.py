import json
from simple_keyword_chatbot import SimpleKeywordChatbot

def test_accuracy():
    """키워드 매칭 정확도 테스트"""
    chatbot = SimpleKeywordChatbot()
    
    # 테스트 케이스들 (정답이 있는 질문들)
    test_cases = [
        {
            "question": "담임선생님과 상담은 어떻게 할 수 있나요?",
            "expected_keywords": ["상담", "담임선생님"],
            "category": "상담"
        },
        {
            "question": "방과후 어디서 해?",
            "expected_keywords": ["방과후"],
            "category": "방과후"
        },
        {
            "question": "오늘의 급식은?",
            "expected_keywords": ["급식"],
            "category": "급식"
        },
        {
            "question": "학교폭력 관련하여 상담이 하고 싶어요",
            "expected_keywords": ["학교폭력", "상담"],
            "category": "학교폭력"
        },
        {
            "question": "등하교시 학생 피드 가능한 곳이 있나요?",
            "expected_keywords": ["등하교"],
            "category": "등하교"
        },
        {
            "question": "전학 가려면 어떻게 해요?",
            "expected_keywords": ["전학"],
            "category": "전학"
        },
        {
            "question": "결석신고서는 어디서 볼 수 있나요?",
            "expected_keywords": ["결석"],
            "category": "결석"
        },
        {
            "question": "로또 당첨번호 알려줘",
            "expected_keywords": [],
            "category": "부적절"
        },
        {
            "question": "날씨 어때?",
            "expected_keywords": [],
            "category": "부적절"
        },
        {
            "question": "와석초등학교 위치가 어디인가요?",
            "expected_keywords": ["와석초", "위치"],
            "category": "학교정보"
        }
    ]
    
    print("=== 키워드 매칭 정확도 테스트 ===\n")
    
    correct_matches = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected_keywords = test_case["expected_keywords"]
        category = test_case["category"]
        
        # 챗봇 응답
        response, confidence = chatbot.find_similar_question(question)
        
        # 정확도 판단
        is_correct = False
        if category == "부적절":
            # 부적절한 질문은 매칭되지 않아야 함
            is_correct = confidence < 0.3
        else:
            # 적절한 질문은 매칭되어야 함
            is_correct = confidence >= 0.3
        
        if is_correct:
            correct_matches += 1
            status = "✅ 정확"
        else:
            status = "❌ 오답"
        
        print(f"{i}. 질문: {question}")
        print(f"   카테고리: {category}")
        print(f"   기대 키워드: {expected_keywords}")
        print(f"   응답: {response[:50]}...")
        print(f"   매칭 점수: {confidence:.2f}")
        print(f"   결과: {status}")
        print("-" * 60)
    
    accuracy = (correct_matches / total_tests) * 100
    print(f"\n=== 정확도 결과 ===")
    print(f"총 테스트: {total_tests}개")
    print(f"정확한 답변: {correct_matches}개")
    print(f"정확도: {accuracy:.1f}%")
    
    # 세부 분석
    print(f"\n=== 세부 분석 ===")
    print("✅ 장점:")
    print("- 빠른 응답 속도 (모델 로딩 없음)")
    print("- 메모리 사용량 최소화")
    print("- Render 무료 플랜 호환")
    print("- 명확한 키워드 매칭")
    
    print("\n⚠️  한계:")
    print("- 동의어/유사어 인식 부족")
    print("- 문맥 이해 능력 제한")
    print("- 복잡한 질문 처리 어려움")
    print("- 키워드가 없는 질문 매칭 실패")

if __name__ == "__main__":
    test_accuracy() 