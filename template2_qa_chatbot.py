import sqlite3
import re
import jieba
import numpy as np
import json
from collections import Counter
from typing import List, Tuple

class QAChatbot:
    def __init__(self):
        """Q-A-chatbot 방식의 챗봇 (TF-IDF 기반)"""
        self.qa_data = self.load_qa_data()
        self.question_vectors = None
        self.vocabulary = None
        self.idf = None
        self.fit_vectorizer()
    
    def load_qa_data(self) -> List[Tuple[str, str, str]]:
        """DB에서 질문-답변 데이터 로드"""
        try:
            # JSON 파일에서 데이터 로드
            with open('school_dataset.json', 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                return [(item['category'], item['question'], item['answer']) for item in json_data]
        except:
            # DB에서 데이터 로드 (fallback)
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
    
    def tokenize(self, text: str) -> List[str]:
        """한국어 텍스트 토크나이징"""
        # jieba로 토크나이징 (한국어 지원)
        tokens = jieba.lcut(text)
        # 불용어 제거
        stopwords = {'은', '는', '이', '가', '을', '를', '에', '의', '도', '로', '과', '와', '에서', '에게', '한', '하다', '있다', '어떻게', '무엇', '어디', '언제', '왜', '누구', '그', '저', '이', '그', '저', '것', '수', '등', '및', '또는', '그리고', '하지만', '그런데', '그러나'}
        return [token for token in tokens if token not in stopwords and len(token) > 1]
    
    def fit_vectorizer(self):
        """TF-IDF 벡터라이저 학습"""
        questions = [qa[1] for qa in self.qa_data]
        
        # 모든 질문 토크나이징
        all_tokens = []
        tokenized_questions = []
        
        for question in questions:
            tokens = self.tokenize(question)
            tokenized_questions.append(tokens)
            all_tokens.extend(tokens)
        
        # 어휘 사전 생성
        self.vocabulary = list(set(all_tokens))
        
        # IDF 계산
        doc_count = len(tokenized_questions)
        self.idf = {}
        for word in self.vocabulary:
            doc_freq = sum(1 for tokens in tokenized_questions if word in tokens)
            self.idf[word] = np.log(doc_count / (doc_freq + 1))
        
        # TF-IDF 벡터 생성
        self.question_vectors = []
        for tokens in tokenized_questions:
            vector = np.zeros(len(self.vocabulary))
            word_count = Counter(tokens)
            
            for i, word in enumerate(self.vocabulary):
                if word in word_count:
                    tf = word_count[word] / len(tokens)
                    vector[i] = tf * self.idf[word]
            
            self.question_vectors.append(vector)
        
        self.question_vectors = np.array(self.question_vectors)
    
    def cosine_similarity(self, vec1, vec2):
        """코사인 유사도 계산"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2) if norm1 * norm2 != 0 else 0
    
    def find_similar_question(self, user_question: str, threshold: float = 0.05) -> Tuple[str, float]:
        """TF-IDF 기반 유사 질문 찾기"""
        # 사용자 질문 벡터화
        user_tokens = self.tokenize(user_question)
        user_vector = np.zeros(len(self.vocabulary))
        word_count = Counter(user_tokens)
        
        for i, word in enumerate(self.vocabulary):
            if word in word_count:
                tf = word_count[word] / len(user_tokens) if user_tokens else 0
                user_vector[i] = tf * self.idf.get(word, 0)
        
        # 코사인 유사도 계산
        similarities = [self.cosine_similarity(user_vector, q_vec) for q_vec in self.question_vectors]
        
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
        
        if confidence > 0.1:
            return f"{answer}\n\n(유사도: {confidence:.2f})"
        else:
            return answer

# 테스트 함수
def test_qa_chatbot():
    """Q-A-chatbot 방식 테스트"""
    chatbot = QAChatbot()
    
    test_questions = [
        "담임선생님과 상담은 어떻게 할 수 있나요?",
        "방과후 어디서 해?",
        "오늘의 급식은?",
        "학교폭력 관련하여 상담이 하고 싶어요",
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