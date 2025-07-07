import json
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

class AIBasedChatbot:
    def __init__(self, dataset_file: str = "school_dataset.json"):
        """AI-based-Chatbot 방식의 챗봇"""
        self.dataset_file = dataset_file
        self.qa_data = self.load_dataset()
        
    def load_dataset(self) -> List[Dict]:
        """학교 데이터를 JSON 형태로 변환하여 로드"""
        try:
            with open(self.dataset_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 기존 DB 데이터를 JSON으로 변환
            return self.convert_db_to_json()
    
    def convert_db_to_json(self) -> List[Dict]:
        """기존 SQLite DB 데이터를 JSON 형태로 변환"""
        import sqlite3
        
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT category, question, answer FROM qa_data')
        rows = cursor.fetchall()
        
        qa_data = []
        for row in rows:
            category, question, answer = row
            qa_data.append({
                "question": question,
                "answer": answer,
                "category": category
            })
        
        conn.close()
        
        # JSON 파일로 저장
        with open(self.dataset_file, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)
        
        return qa_data
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """문자열 유사도 계산 (SequenceMatcher 사용)"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def find_best_match(self, user_question: str, threshold: float = 0.3) -> Tuple[str, float]:
        """가장 유사한 질문 찾기"""
        processed_question = self.preprocess_text(user_question)
        
        best_match = None
        best_score = 0
        
        for qa in self.qa_data:
            processed_qa_question = self.preprocess_text(qa["question"])
            similarity = self.calculate_similarity(processed_question, processed_qa_question)
            
            if similarity > best_score:
                best_score = similarity
                best_match = qa
        
        if best_score >= threshold:
            return best_match["answer"], best_score
        else:
            return "죄송합니다. 해당 정보는 데이터베이스에 없습니다.", 0.0
    
    def get_response(self, user_question: str) -> str:
        """사용자 질문에 대한 답변 반환"""
        answer, confidence = self.find_best_match(user_question)
        
        if confidence > 0.5:
            return f"{answer}\n\n(신뢰도: {confidence:.2f})"
        else:
            return answer

# 테스트 함수
def test_ai_based_chatbot():
    """AI-based-Chatbot 방식 테스트"""
    chatbot = AIBasedChatbot()
    
    test_questions = [
        "1학년 방과후 수업 시간이 궁금해요",
        "유치원 운영시간은 언제인가요?",
        "담임선생님과 상담하고 싶어요",
        "등하교시 학생 피드 가능한 곳이 있나요?",
        "로또 당첨번호 알려줘"
    ]
    
    print("=== AI-based-Chatbot 방식 테스트 ===")
    for question in test_questions:
        print(f"\n질문: {question}")
        response = chatbot.get_response(question)
        print(f"답변: {response}")
        print("-" * 50)

if __name__ == "__main__":
    test_ai_based_chatbot() 