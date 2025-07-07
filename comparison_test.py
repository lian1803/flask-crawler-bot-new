import time
from template1_ai_based_chatbot import AIBasedChatbot
from template2_qa_chatbot import QAChatbot
from ai_logic import AILogic  # 기존 방식

def run_comparison_test():
    """3가지 방식 비교 테스트"""
    
    # 챗봇 인스턴스 생성
    print("챗봇 초기화 중...")
    chatbot1 = AIBasedChatbot()  # AI-based-Chatbot 방식
    chatbot2 = QAChatbot()       # Q-A-chatbot 방식 (TF-IDF)
    chatbot3 = AILogic()         # 기존 OpenAI GPT 방식
    
    # 테스트 질문들
    test_questions = [
        "1학년 방과후 수업 시간이 궁금해요",
        "유치원 운영시간은 언제인가요?",
        "담임선생님과 상담하고 싶어요",
        "등하교시 학생 피드 가능한 곳이 있나요?",
        "로또 당첨번호 알려줘",
        "와석초 방과후 프로그램",
        "유치원 교육비는 얼마인가요?",
        "학교 시설 사용 안내"
    ]
    
    print("\n" + "="*80)
    print("3가지 챗봇 방식 비교 테스트")
    print("="*80)
    
    results = {
        "AI-based-Chatbot": {"responses": [], "times": []},
        "Q-A-chatbot (TF-IDF)": {"responses": [], "times": []},
        "OpenAI GPT": {"responses": [], "times": []}
    }
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n\n[테스트 {i}] 질문: {question}")
        print("-" * 60)
        
        # 1. AI-based-Chatbot 방식
        start_time = time.time()
        try:
            response1 = chatbot1.get_response(question)
            time1 = time.time() - start_time
            results["AI-based-Chatbot"]["responses"].append(response1)
            results["AI-based-Chatbot"]["times"].append(time1)
            print(f"1️⃣ AI-based-Chatbot: {response1[:100]}... (응답시간: {time1:.2f}초)")
        except Exception as e:
            print(f"1️⃣ AI-based-Chatbot: 오류 발생 - {e}")
            results["AI-based-Chatbot"]["responses"].append("오류")
            results["AI-based-Chatbot"]["times"].append(0)
        
        # 2. Q-A-chatbot 방식
        start_time = time.time()
        try:
            response2 = chatbot2.get_response(question)
            time2 = time.time() - start_time
            results["Q-A-chatbot (TF-IDF)"]["responses"].append(response2)
            results["Q-A-chatbot (TF-IDF)"]["times"].append(time2)
            print(f"2️⃣ Q-A-chatbot (TF-IDF): {response2[:100]}... (응답시간: {time2:.2f}초)")
        except Exception as e:
            print(f"2️⃣ Q-A-chatbot (TF-IDF): 오류 발생 - {e}")
            results["Q-A-chatbot (TF-IDF)"]["responses"].append("오류")
            results["Q-A-chatbot (TF-IDF)"]["times"].append(0)
        
        # 3. OpenAI GPT 방식
        start_time = time.time()
        try:
            success, response3 = chatbot3.process_message(question, "test_user")
            time3 = time.time() - start_time
            results["OpenAI GPT"]["responses"].append(response3)
            results["OpenAI GPT"]["times"].append(time3)
            print(f"3️⃣ OpenAI GPT: {response3[:100]}... (응답시간: {time3:.2f}초)")
        except Exception as e:
            print(f"3️⃣ OpenAI GPT: 오류 발생 - {e}")
            results["OpenAI GPT"]["responses"].append("오류")
            results["OpenAI GPT"]["times"].append(0)
    
    # 결과 요약
    print("\n\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)
    
    for method, data in results.items():
        avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else 0
        error_count = data["responses"].count("오류")
        success_count = len(data["responses"]) - error_count
        
        print(f"\n🔍 {method}:")
        print(f"   ✅ 성공: {success_count}/{len(data['responses'])}")
        print(f"   ❌ 오류: {error_count}/{len(data['responses'])}")
        print(f"   ⏱️  평균 응답시간: {avg_time:.2f}초")
    
    print("\n" + "="*80)
    print("🎯 권장사항:")
    print("1. 응답시간이 빠른 방식: Q-A-chatbot (TF-IDF)")
    print("2. 정확도가 높은 방식: AI-based-Chatbot")
    print("3. 자연스러운 답변: OpenAI GPT")
    print("="*80)

if __name__ == "__main__":
    run_comparison_test() 