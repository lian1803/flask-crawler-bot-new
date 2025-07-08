import json
import re
from typing import List, Tuple

class SimpleKeywordChatbot:
    def __init__(self):
        """간단한 키워드 기반 챗봇"""
        self.qa_data = self.load_qa_data()
    
    def load_qa_data(self) -> List[dict]:
        """JSON 파일에서 데이터 로드"""
        with open('school_dataset.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def find_similar_question(self, user_question: str) -> Tuple[str, float]:
        """키워드 기반 유사 질문 찾기"""
        user_question_lower = user_question.lower()
        
        best_match = None
        best_score = 0
        
        for qa in self.qa_data:
            question_lower = qa['question'].lower()
            
            # 키워드 매칭 점수 계산
            score = 0
            common_words = set(user_question_lower.split()) & set(question_lower.split())
            score += len(common_words) * 0.3
            
            # 부분 문자열 매칭
            if any(word in question_lower for word in user_question_lower.split()):
                score += 0.2
            
            # 정확한 키워드 매칭
            important_keywords = ['상담', '방과후', '급식', '학교폭력', '등하교', '전학', '결석']
            for keyword in important_keywords:
                if keyword in user_question_lower and keyword in question_lower:
                    score += 0.5
            
            if score > best_score:
                best_score = score
                best_match = qa
        
        if best_score > 0.3:
            return best_match['answer'], best_score
        else:
            return "죄송합니다. 해당 정보는 데이터베이스에 없습니다.", 0.0
    
    def get_response(self, user_question: str) -> str:
        """사용자 질문에 대한 답변 반환"""
        answer, confidence = self.find_similar_question(user_question)
        
        if confidence > 0.3:
            return f"{answer}\n\n(매칭 점수: {confidence:.2f})"
        else:
            return answer

# 테스트 함수
def test_simple_chatbot():
    """간단한 키워드 챗봇 테스트"""
    chatbot = SimpleKeywordChatbot()
    
    test_questions = [
        "담임선생님과 상담은 어떻게 할 수 있나요?",
        "방과후 어디서 해?",
        "오늘의 급식은?",
        "학교폭력 관련하여 상담이 하고 싶어요",
        "등하교시 학생 피드 가능한 곳이 있나요?",
        "로또 당첨번호 알려줘"
    ]
    
    print("=== 간단한 키워드 챗봇 테스트 ===")
    for question in test_questions:
        print(f"\n질문: {question}")
        response = chatbot.get_response(question)
        print(f"답변: {response}")
        print("-" * 50)

if __name__ == "__main__":
    test_simple_chatbot() 