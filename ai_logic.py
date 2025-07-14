import openai
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
from config import OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE, MAX_TOKENS, TOP_P, BAN_WORDS
from database import DatabaseManager

class AILogic:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.db = DatabaseManager()
        self.qa_data = None
        self.load_qa_data()
        
    def load_qa_data(self):
        """QA 데이터 로드"""
        try:
            # JSON 파일에서 데이터 로드
            with open('school_dataset.json', 'r', encoding='utf-8') as f:
                self.qa_data = json.load(f)
        except:
            # DB에서 데이터 로드 (fallback)
            self.qa_data = self.db.get_qa_data()
    
    def is_banned_content(self, text: str) -> bool:
        """금지된 내용인지 확인 (학교 관련 문의는 예외)"""
        text_lower = text.lower()
        
        # 학교 관련 문의는 허용
        school_inquiry_keywords = ['학교폭력', '상담', '문의', '도움', '안내']
        if any(keyword in text for keyword in school_inquiry_keywords):
            return False
            
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
        """와석초 관련 질문인지 판별 (키워드 기반)"""
        # 기본 학교 관련 키워드
        school_keywords = [
            '와석초', '학교', '선생', '교사', '학년', '반', '학생', '급식', '식단', '방과후', 
            '하교', '등교', '교실', '학사', '수업', '상담', '교무실', '교장', '교감', '유치원', 
            '돌봄', '학부모', '행정실', '시설', '공지', '알림', '방학', '전학', '입학', '졸업', 
            '체험', '결석', '출석', '신청', '교재', '교과서', '도서실', '분실물', '쉼터', '늘봄'
        ]
        
        # 질문 패턴 (학교 관련 질문임을 나타내는 단어들)
        question_patterns = [
            '언제', '어디서', '어떻게', '몇시', '얼마', '무엇', '누구', '왜', '어떤',
            '절차', '신청', '발급', '연락', '문의', '안내', '정보', '위치', '시간', '비용'
        ]
        # 추가 패턴 (학교 행정/서류/사진 등)
        extra_patterns = [
            '필요한 서류', '기간', '방법', '연락처', '재발급', '첨부', '사진', '파일', '양식', '증명서', '신청서', '보고서'
        ]
        if any(p in text for p in extra_patterns):
            return True
        
        # QA DB에서 키워드 매칭 확인
        try:
            if self.qa_data:
                text_lower = text.lower()
                for qa in self.qa_data:
                    question_lower = qa['question'].lower()
                    # 중요 키워드 매칭
                    important_keywords = ['상담', '방과후', '급식', '학교폭력', '등하교', '전학', '결석']
                    for keyword in important_keywords:
                        if keyword in text_lower and keyword in question_lower:
                            return True
        except Exception:
            pass
        
        has_school_keyword = any(k in text for k in school_keywords)
        has_question_pattern = any(p in text for p in question_patterns)
        return has_school_keyword or has_question_pattern

    def find_qa_match(self, user_message: str, threshold: float = 0.15) -> Optional[Dict]:
        """QA 데이터베이스에서 유사한 질문 찾기 (향상된 키워드 기반)"""
        if not self.qa_data:
            return None
        
        try:
            user_message_lower = user_message.lower()
            best_match = None
            best_score = 0
            
            for qa in self.qa_data:
                question_lower = qa['question'].lower()
                
                # 1. 기본 키워드 매칭 점수
                score = 0
                user_words = set(user_message_lower.split())
                question_words = set(question_lower.split())
                common_words = user_words & question_words
                score += len(common_words) * 0.4
                
                # 2. 부분 문자열 매칭 (더 관대하게)
                for word in user_words:
                    if len(word) > 1 and word in question_lower:
                        score += 0.3
                
                # 3. 중요 키워드 가중치
                important_keywords = [
                    '상담', '방과후', '급식', '학교폭력', '등하교', '전학', '결석',
                    '유치원', '초등', '학교', '학부모', '학생', '선생님', '교사',
                    '시간', '언제', '어디서', '어떻게', '신청', '문의', '안내'
                ]
                for keyword in important_keywords:
                    if keyword in user_message_lower and keyword in question_lower:
                        score += 0.6
                
                # 4. 카테고리별 특화 키워드
                category_keywords = {
                    '초등': ['학년', '반', '교실', '수업', '하교', '등교'],
                    '유치원': ['유치원', '원아', '원생', '하원', '등원'],
                    '첨부파일': ['이미지', '파일', '참조', '첨부', '사진']
                }
                
                for category, keywords in category_keywords.items():
                    if qa.get('category') == category:
                        for keyword in keywords:
                            if keyword in user_message_lower:
                                score += 0.4
                
                # 5. 문장 길이 보정 (짧은 질문에 유리하게)
                if len(user_words) <= 3:
                    score += 0.3
                
                # 6. 단일 키워드 매칭 (매우 짧은 질문)
                if len(user_words) == 1:
                    for word in user_words:
                        if word in question_lower:
                            score += 0.4
                
                # 7. 부분 매칭 보너스
                for word in user_words:
                    if len(word) > 2:
                        for q_word in question_words:
                            if word in q_word or q_word in word:
                                score += 0.2
                
                if score > best_score:
                    best_score = score
                    best_match = qa
            
            if best_score >= threshold:
                return best_match
        except Exception as e:
            print(f"QA 매칭 중 오류: {e}")
        return None
    
    def get_date_from_message(self, text: str) -> Optional[str]:
        """메시지에서 날짜 추출"""
        today = datetime.now()
        
        # 상대적 날짜 표현
        if "오늘" in text:
            return today.strftime("%Y-%m-%d")
        if "내일" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if "어제" in text:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        if "모레" in text:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        if "글피" in text:
            return (today + timedelta(days=3)).strftime("%Y-%m-%d")
        
        # "5월 20일", "5/20" 같은 패턴 찾기 (더 정확한 패턴)
        match = re.search(r'(\d{1,2})[월\s/](\d{1,2})일?', text)
        if match:
            month, day = map(int, match.groups())
            # 현재 연도 기준으로 날짜 생성
            try:
                target_date = today.replace(month=month, day=day)
                return target_date.strftime("%Y-%m-%d")
            except ValueError:
                # 잘못된 날짜인 경우 None 반환
                return None
        
        # "2024년 5월 20일" 같은 패턴 찾기
        match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일?', text)
        if match:
            year, month, day = map(int, match.groups())
            try:
                target_date = datetime(year, month, day)
                return target_date.strftime("%Y-%m-%d")
            except ValueError:
                return None
        
        return None
    
    def get_meal_info(self, date: str) -> str:
        """식단 정보 조회"""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            weekday = target_date.weekday()
            
            # 주말 체크
            if weekday >= 5:  # 토요일(5), 일요일(6)
                weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                return f"{date}({weekday_names[weekday]})는 주말이라 급식이 없습니다."
            
            # 실제 급식 데이터 조회
            menu = self.db.get_meal_info(date)
            if menu:
                weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                return f"{date}({weekday_names[weekday]}) 중식 메뉴입니다:\n\n{menu}"
            else:
                weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                return f"{date}({weekday_names[weekday]})에는 식단 정보가 아직 등록되지 않았습니다."
                
        except ValueError as e:
            return f"날짜 형식 오류: {date}"
        except Exception as e:
            return f"식단 정보 조회 중 오류가 발생했습니다: {str(e)}"
    
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
            # 급식 관련 질문에서만 날짜 추출 (오늘, 내일, 어제, 모레 등)
            date = self.get_date_from_message(user_message)
            
            # 날짜가 명시된 경우 (오늘, 내일, 어제, 모레, 구체적 날짜)
            if date:
                response = self.get_meal_info(date)
                self.db.save_conversation(user_id, user_message, response)
                return True, response
            
            # 날짜가 명시되지 않은 급식 관련 질문은 QA 데이터베이스에서 답변
            qa_match = self.find_qa_match(user_message)
            if qa_match:
                response = qa_match['answer']
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
            
            response = openai.chat.completions.create(
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