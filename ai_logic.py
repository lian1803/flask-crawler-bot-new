import openai
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE, MAX_TOKENS, TOP_P, BAN_WORDS
from database import DatabaseManager

class AILogic:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.db = DatabaseManager()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def is_banned_content(self, text: str) -> bool:
        """금지된 내용인지 확인"""
        text_lower = text.lower()
        return any(word in text_lower for word in BAN_WORDS)
    
    def get_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return """당신은 와석초등학교의 친근하고 도움이 되는 챗봇입니다. 
다음 규칙을 따라주세요:

1. 항상 친근하고 정중하게 응답하세요
2. 학교 관련 질문에 대해 정확한 정보를 제공하세요
3. 모르는 내용은 솔직히 모른다고 말하세요
4. 한국어로 응답하세요
5. 답변은 간결하고 명확하게 작성하세요
6. 사용자가 학교 관련 정보를 요청하면 데이터베이스에서 찾아서 제공하세요

학교 정보:
- 학교명: 와석초등학교
- 위치: 경기도
- 주요 서비스: 급식 정보, 공지사항, 학교 생활 안내"""
    
    def build_conversation_context(self, user_id: str, current_message: str) -> List[Dict]:
        """대화 컨텍스트 구축"""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # 최근 대화 히스토리 가져오기
        history = self.db.get_conversation_history(user_id, limit=3)
        
        for conv in reversed(history):  # 시간순으로 정렬
            messages.append({"role": "user", "content": conv['message']})
            messages.append({"role": "assistant", "content": conv['response']})
        
        # 현재 메시지 추가
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def find_qa_match(self, user_message: str, threshold: float = 0.3) -> Optional[Dict]:
        """QA 데이터베이스에서 유사한 질문 찾기"""
        qa_data = self.db.get_qa_data()
        
        if not qa_data:
            return None
        
        # 질문들만 추출
        questions = [qa['question'] for qa in qa_data]
        
        if not questions:
            return None
        
        try:
            # TF-IDF 벡터화
            tfidf_matrix = self.vectorizer.fit_transform([user_message] + questions)
            
            # 유사도 계산
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            # 가장 유사한 질문 찾기
            max_similarity = similarities[0].max()
            max_index = similarities[0].argmax()
            
            if max_similarity >= threshold:
                return qa_data[max_index]
            
        except Exception as e:
            print(f"QA 매칭 중 오류: {e}")
        
        return None
    
    def get_date_from_message(self, text: str) -> Optional[str]:
        """메시지에서 날짜 추출"""
        today = datetime.now()
        
        if "오늘" in text:
            return today.strftime("%Y-%m-%d")
        if "내일" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if "어제" in text:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        if "모레" in text:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # "5월 20일", "5/20" 같은 패턴 찾기
        match = re.search(r'(\d{1,2})[월/\s](\d{1,2})일?', text)
        if match:
            month, day = map(int, match.groups())
            return today.replace(month=month, day=day).strftime("%Y-%m-%d")
        
        return None
    
    def get_meal_info(self, date: str) -> str:
        """식단 정보 조회"""
        weekday = datetime.strptime(date, "%Y-%m-%d").weekday()
        if weekday >= 5:  # 주말
            return f"{date}는 주말(토/일)이라 급식이 없습니다."
        
        menu = self.db.get_meal_info(date)
        if menu:
            return f"{date} 중식 메뉴입니다:\n\n{menu}"
        return f"{date}에는 식단 정보가 없습니다."
    
    def get_notices_info(self) -> str:
        """공지사항 정보 조회"""
        notices = self.db.get_latest_notices(limit=3)
        if not notices:
            return "현재 등록된 공지사항이 없습니다."
        
        result = "최신 공지사항입니다:\n\n"
        for notice in notices:
            result += f"📢 {notice['title']}\n"
            if notice['content']:
                result += f"   {notice['content'][:50]}...\n"
            result += f"   작성일: {notice['created_at']}\n\n"
        
        return result
    
    def process_message(self, user_message: str, user_id: str) -> Tuple[bool, str]:
        """메인 메시지 처리 로직"""
        print(f"사용자 메시지: {user_message}")
        
        # 금지된 내용 확인
        if self.is_banned_content(user_message):
            return False, "부적절한 내용이 포함되어 있습니다. 다른 질문을 해주세요."
        
        # 1. 식단 관련 질문 확인
        if any(keyword in user_message for keyword in ["급식", "식단", "밥", "점심", "메뉴"]):
            date = self.get_date_from_message(user_message)
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            response = self.get_meal_info(date)
            self.db.save_conversation(user_id, user_message, response)
            return True, response
        
        # 2. 공지사항 관련 질문 확인
        if any(keyword in user_message for keyword in ["공지", "알림", "소식", "뉴스"]):
            response = self.get_notices_info()
            self.db.save_conversation(user_id, user_message, response)
            return True, response
        
        # 3. QA 데이터베이스에서 유사한 질문 찾기
        qa_match = self.find_qa_match(user_message)
        if qa_match:
            response = qa_match['answer']
            if qa_match['additional_answer']:
                response += f"\n\n추가 정보:\n{qa_match['additional_answer']}"
            
            self.db.save_conversation(user_id, user_message, response)
            return True, response
        
        # 4. OpenAI를 통한 일반적인 응답
        try:
            messages = self.build_conversation_context(user_id, user_message)
            
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                top_p=TOP_P
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 응답이 너무 길면 자르기
            if len(ai_response) > 200:
                ai_response = ai_response[:200] + "..."
            
            self.db.save_conversation(user_id, user_message, ai_response)
            return True, ai_response
            
        except Exception as e:
            print(f"OpenAI 처리 중 오류: {e}")
            fallback_response = "죄송합니다. 현재 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요."
            self.db.save_conversation(user_id, user_message, fallback_response)
            return False, fallback_response 