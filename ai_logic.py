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
2. 반드시 아래 제공된 학교 데이터베이스 정보만을 참고해서 답변하세요
3. 데이터베이스에 없는 정보는 "죄송합니다. 해당 정보는 데이터베이스에 없습니다."라고 답변하세요
4. 한국어로 응답하세요
5. 답변은 간결하고 명확하게 작성하세요
6. 일반적인 대화나 학교와 관련 없는 질문에는 "와석초등학교 관련 질문에만 답변할 수 있습니다."라고 답변하세요

학교 정보:
- 학교명: 와석초등학교
- 위치: 경기도
- 주요 서비스: 급식 정보, 공지사항, 학교 생활 안내"""
    
    def build_conversation_context(self, user_id: str, current_message: str) -> List[Dict]:
        """대화 컨텍스트 구축"""
        # 학교 데이터베이스 정보 가져오기
        qa_data = self.db.get_qa_data()
        school_info = "와석초등학교 관련 정보:\n"
        
        for qa in qa_data[:10]:  # 최대 10개 QA 정보만 포함
            school_info += f"Q: {qa['question']}\nA: {qa['answer']}\n\n"
        
        system_prompt = self.get_system_prompt() + "\n\n" + school_info
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 최근 대화 히스토리 가져오기
        history = self.db.get_conversation_history(user_id, limit=3)
        
        for conv in reversed(history):  # 시간순으로 정렬
            messages.append({"role": "user", "content": conv['message']})
            messages.append({"role": "assistant", "content": conv['response']})
        
        # 현재 메시지 추가
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def preprocess_question(self, text: str) -> str:
        """질문 전처리: 소문자화, 특수문자 제거, 불용어 제거 등"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        # 불용어 예시(확장 가능)
        stopwords = ['은', '는', '이', '가', '을', '를', '에', '의', '도', '로', '과', '와', '에서', '에게', '한', '하다', '있다', '어떻게', '무엇', '어디', '언제', '왜', '누구']
        for sw in stopwords:
            text = text.replace(sw, '')
        return text.strip()

    def is_school_related(self, text: str) -> bool:
        """와석초 관련 질문인지 판별 (학교명, 교사, 학년, 반, 급식, 방과후 등 키워드 포함)"""
        keywords = [
            '와석초', '학교', '선생', '교사', '학년', '반', '학생', '급식', '식단', '방과후', '하교', '등교', '교실', '학사', '수업', '상담', '교무실', '교장', '교감', '유치원', '돌봄', '학부모', '행정실', '시설', '공지', '알림', '방학', '전학', '입학', '졸업', '체험', '결석', '출석', '신청', '수업', '교재', '교과서', '도서실', '분실물', '쉼터', '늘봄', '특수학급', '특성화', '참여수업', '학부모', '학사일정', '학교생활', '학교장', '학교시설', '학교운영', '학교행사', '학교공지', '학교소식', '학교뉴스', '학교정보', '학교위치', '학교주소', '학교전화', '학교연락처', '학교홈페이지', '학교사이트', '학교웹사이트', '학교이메일', '학교팩스', '학교교무실', '학교행정실', '학교도서실', '학교체육관', '학교운동장', '학교강당', '학교식당', '학교매점', '학교분실물', '학교쉼터', '학교늘봄', '학교특수학급', '학교특성화', '학교참여수업', '학교학부모', '학교학사일정', '학교생활', '학교장', '학교시설', '학교운영', '학교행사', '학교공지', '학교소식', '학교뉴스', '학교정보', '학교위치', '학교주소', '학교전화', '학교연락처', '학교홈페이지', '학교사이트', '학교웹사이트', '학교이메일', '학교팩스', '학교교무실', '학교행정실', '학교도서실', '학교체육관', '학교운동장', '학교강당', '학교식당', '학교매점', '학교분실물', '학교쉼터', '학교늘봄', '학교특수학급', '학교특성화', '학교참여수업', '학교학부모', '학교학사일정', '학교생활'
        ]
        return any(k in text for k in keywords)

    def find_qa_match(self, user_message: str, threshold: float = 0.2) -> Optional[Dict]:
        """QA 데이터베이스에서 유사한 질문 찾기 (임계값 완화, 전처리 적용)"""
        qa_data = self.db.get_qa_data()
        if not qa_data:
            return None
        questions = [self.preprocess_question(qa['question']) for qa in qa_data]
        user_message_prep = self.preprocess_question(user_message)
        if not questions:
            return None
        try:
            tfidf_matrix = self.vectorizer.fit_transform([user_message_prep] + questions)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
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
        
        # 와석초 관련 질문인지 판별
        if not self.is_school_related(user_message):
            return False, "와석초등학교 관련 질문에만 답변할 수 있습니다."
        
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
            if qa_match.get('additional_answer'):
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