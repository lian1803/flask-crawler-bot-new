import sqlite3
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple

class QAChatbot:
    def __init__(self):
        """Q-A-chatbot 방식의 챗봇 (TF-IDF 기반)"""
        self.qa_data = self.load_qa_data()
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,
            ngram_range=(1, 2)
        )
        self.question_vectors = None
        self.fit_vectorizer()
    
    def load_qa_data(self) -> List[Tuple[str, str, str]]:
        """DB에서 질문-답변 데이터 로드"""
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT category, question, answer FROM qa_data')
        rows = cursor.fetchall()
        
        conn.close()
        return rows
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
    
    def fit_vectorizer(self):
        """TF-IDF 벡터라이저 학습"""
        questions = [self.preprocess_text(qa[1]) for qa in self.qa_data]
        self.question_vectors = self.vectorizer.fit_transform(questions)
    
    def find_similar_question(self, user_question: str, threshold: float = 0.2) -> Tuple[str, float]:
        """TF-IDF 기반 유사 질문 찾기"""
        processed_question = self.preprocess_text(user_question)
        
        # 사용자 질문을 벡터화
        user_vector = self.vectorizer.transform([processed_question])
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(user_vector, self.question_vectors).flatten()
        
        # 가장 유사한 질문 찾기
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            return self.qa_data[best_idx][2], best_score  # answer, score
        else:
            return "죄송합니다. 해당 정보는 데이터베이스에 없습니다.", 0.0
    
    def get_response(self, user_question: str) -> str:
        """사용자 질문에 대한 답변 반환"""
        answer, confidence = self.find_similar_question(user_question)
        
        if confidence > 0.3:
            return f"{answer}\n\n(유사도: {confidence:.2f})"
        else:
            return answer

# 테스트 함수
def test_qa_chatbot():
    """Q-A-chatbot 방식 테스트"""
    chatbot = QAChatbot()
    
    test_questions = [
        "1학년 방과후 수업 시간이 궁금해요",
        "유치원 운영시간은 언제인가요?",
        "담임선생님과 상담하고 싶어요",
        "등하교시 학생 피드 가능한 곳이 있나요?",
        "로또 당첨번호 알려줘"
    ]
    
    print("=== Q-A-chatbot 방식 테스트 (TF-IDF) ===")
    for question in test_questions:
        print(f"\n질문: {question}")
        response = chatbot.get_response(question)
        print(f"답변: {response}")
        print("-" * 50)

if __name__ == "__main__":
    test_qa_chatbot() 