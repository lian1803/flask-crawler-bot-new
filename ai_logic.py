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
        """대화 컨텍스트 구축 (최적화된 버전)"""
        # 간단한 시스템 프롬프트만 사용
        system_prompt = self.get_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 최근 대화 히스토리는 1개만 가져오기 (성능 향상)
        history = self.db.get_conversation_history(user_id, limit=1)
        
        for conv in reversed(history):
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
        """와석초등학교 관련 질문인지 판별 (개선된 버전)"""
        text_lower = text.lower()
        
        # 학교 관련 키워드 (확장된 목록)
        school_keywords = [
            # 학교 기본 정보
            '와석', '와석초', '와석초등학교', '학교', '초등학교',
            
            # 학사 관련
            '개학', '방학', '졸업', '입학', '전학', '전입', '전출',
            '학사일정', '학사', '일정', '스케줄', '시험', '시험일',
            
            # 급식 관련 (맥락적 표현 포함)
            '급식', '식단', '점심', '중식', '메뉴', '밥', '식사', '밥상',
            '먹어', '먹었어', '먹었어요', '먹었냐', '나와', '나와요', '나오냐',
            
            # 방과후 관련
            '방과후', '방과후학교', '늘봄교실', '돌봄교실', '특기적성',
            
            # 교실/학급 관련
            '교실', '학급', '반', '담임', '선생님', '교사', '학년',
            
            # 등하교 관련
            '등교', '하교', '등하교', '정차대', '버스', '통학',
            
            # 학교시설 관련
            '체육관', '운동장', '도서관', '도서실', '보건실', '급식실',
            '컴퓨터실', '음악실', '미술실', '학교시설',
            
            # 상담/문의 관련
            '상담', '문의', '연락', '전화', '전화번호', '연락처', '얘기', '만나',
            
            # 결석/출석 관련
            '결석', '출석', '체험학습', '현장학습', '신고서', '아프면', '병원',
            
            # 유치원 관련
            '유치원', '유아', '원무실', '등원', '하원',
            
            # 일반적인 학교 관련 표현
            '알려줘', '알려주세요', '어디', '언제', '어떻게', '무엇', '왜', '누가', '어떤', '몇',
            '궁금', '필요', '찾고', '도와', '부탁', '얼마', '얼마나', '뭐가', '뭐야', '뭐예요',
            '어디야', '어디예요', '언제야', '언제예요', '어떻게야', '어떻게예요',
            '누구한테', '누구랑', '어디로', '어디서', '언제까지', '얼마나 걸려'
        ]
        
        # 부적절한 내용 키워드
        inappropriate_keywords = [
            '바보', '멍청', '싫어', '화나', '짜증', '죽어', '꺼져',
            '개새끼', '병신', '미친', '돌았', '미쳤'
        ]
        
        # 부적절한 내용이 포함된 경우 거부
        for keyword in inappropriate_keywords:
            if keyword in text_lower:
                return False
        
        # 학교 관련 키워드가 하나라도 포함된 경우 허용
        for keyword in school_keywords:
            if keyword in text_lower:
                return True
        
        # 일반적인 인사나 도움 요청은 허용
        greeting_keywords = ['안녕', '도움', '감사', '고마워', '잘 있어']
        for keyword in greeting_keywords:
            if keyword in text_lower:
                return True
        
        # 와석초와 관련없는 일반적인 질문은 거부
        unrelated_keywords = ['날씨', '주식', '영화', '음식', '여행', '쇼핑', '게임']
        for keyword in unrelated_keywords:
            if keyword in text_lower:
                return False
        
        return False

    def find_qa_match(self, user_message: str, threshold: float = 0.15) -> Optional[Dict]:
        """QA 데이터에서 유사한 질문 찾기 (개선된 버전)"""
        try:
            user_message_lower = user_message.lower().strip()
            best_match = None
            best_score = 0
            
            # 중요 키워드 정의 (맥락적 매칭을 위해 확장)
            important_keywords = [
                "개학", "급식", "방과후", "전학", "상담", "결석", "교실", "등하교",
                "학교시설", "유치원", "전화번호", "연락처", "일정", "시간", "방법",
                "절차", "신청", "등록", "예약", "문의", "알려줘", "알려주세요",
                "어디", "언제", "어떻게", "무엇", "왜", "누가", "어떤", "몇",
                # 맥락적 키워드 추가
                "밥", "점심", "메뉴", "식사", "중식", "밥상", "먹어", "나와",
                "얘기", "만나", "아프면", "병원", "등원", "하원",
                "뭐야", "뭐예요", "어디야", "어디예요", "언제야", "언제예요",
                "어떻게야", "어떻게예요", "얼마야", "얼마예요", "얼마나"
            ]
            
            # 우선순위 QA가 있으면 그것만 확인, 없으면 전체 확인
            qa_list = self.qa_data  # 전체 QA 데이터 확인
            
            for qa in qa_list:
                question_lower = qa['question'].lower()
                
                # 1. 정확한 매칭 (가장 높은 점수)
                if user_message_lower == question_lower:
                    return qa
                
                # 2. 포함 관계 확인
                if user_message_lower in question_lower or question_lower in user_message_lower:
                    score = 0.8
                    if score > best_score:
                        best_score = score
                        best_match = qa
                    continue
                
                # 3. 맥락적 매칭 (새로 추가)
                context_score = self.calculate_context_score(user_message_lower, question_lower)
                if context_score > 0:
                    if context_score > best_score:
                        best_score = context_score
                        best_match = qa
                    continue
                
                # 4. 단어 기반 매칭
                score = 0
                user_words = set(user_message_lower.split())
                question_words = set(question_lower.split())
                
                # 공통 단어 수
                common_words = user_words & question_words
                score += len(common_words) * 0.4
                
                # 중요 키워드 가중치
                for keyword in important_keywords:
                    if keyword in user_message_lower and keyword in question_lower:
                        score += 0.6
                        break
                
                # 부분 문자열 매칭
                for word in user_words:
                    if len(word) > 2:
                        if word in question_lower:
                            score += 0.2
                        # 유사한 단어 매칭 (예: "개학"과 "개학일")
                        for q_word in question_words:
                            if len(q_word) > 2 and (word in q_word or q_word in word):
                                score += 0.1
                
                if score > best_score:
                    best_score = score
                    best_match = qa
            
            if best_score >= threshold:
                return best_match
        except Exception as e:
            print(f"QA 매칭 중 오류: {e}")
        return None
    
    def calculate_context_score(self, user_message: str, question: str) -> float:
        """맥락적 매칭 점수 계산"""
        score = 0
        
        # 급식 관련 맥락 매칭
        meal_contexts = [
            (['밥', '뭐냐', '뭐야', '뭐예요'], ['급식', '식단', '메뉴']),
            (['점심', '뭐냐', '뭐야', '뭐예요'], ['급식', '식단', '메뉴']),
            (['메뉴', '뭐냐', '뭐야', '뭐예요'], ['급식', '식단', '메뉴']),
            (['먹어', '뭐'], ['급식', '식단', '메뉴']),
            (['나와', '뭐'], ['급식', '식단', '메뉴']),
            (['밥상', '뭐냐', '뭐야', '뭐예요'], ['급식', '식단', '메뉴'])
        ]
        
        for user_pattern, question_pattern in meal_contexts:
            if any(word in user_message for word in user_pattern):
                if any(word in question for word in question_pattern):
                    score += 0.7
                    break
        
        # 상담 관련 맥락 매칭
        counseling_contexts = [
            (['얘기', '하고', '싶어'], ['상담']),
            (['만나', '고', '싶어'], ['상담']),
            (['담임', '이랑'], ['상담', '담임']),
            (['선생님', '이랑'], ['상담', '교사'])
        ]
        
        for user_pattern, question_pattern in counseling_contexts:
            if any(word in user_message for word in user_pattern):
                if any(word in question for word in question_pattern):
                    score += 0.6
                    break
        
        # 결석 관련 맥락 매칭
        absence_contexts = [
            (['아프면', '어떻게'], ['결석', '신고']),
            (['병원', '갈', '것', '같으면'], ['결석', '신고']),
            (['몸이', '안', '좋으면'], ['결석', '신고'])
        ]
        
        for user_pattern, question_pattern in absence_contexts:
            if any(word in user_message for word in user_pattern):
                if any(word in question for word in question_pattern):
                    score += 0.6
                    break
        
        # 교실 관련 맥락 매칭
        classroom_contexts = [
            (['어디야', '어디예요'], ['교실', '배치', '위치']),
            (['찾고', '있어'], ['교실', '배치', '위치']),
            (['어떻게', '가'], ['교실', '배치', '위치'])
        ]
        
        for user_pattern, question_pattern in classroom_contexts:
            if any(word in user_message for word in user_pattern):
                if any(word in question for word in question_pattern):
                    score += 0.5
                    break
        
        # 등하교 관련 맥락 매칭
        commute_contexts = [
            (['언제야', '언제예요'], ['등교', '하교', '시간']),
            (['몇시야', '몇시예요'], ['등교', '하교', '시간']),
            (['어떻게', '가'], ['등교', '하교', '방법'])
        ]
        
        for user_pattern, question_pattern in commute_contexts:
            if any(word in user_message for word in user_pattern):
                if any(word in question for word in question_pattern):
                    score += 0.5
                    break
        
        return score
    
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
        """메인 메시지 처리 로직 (최적화된 버전)"""
        print(f"사용자 메시지: {user_message}")
        
        # 금지된 내용 확인
        if self.is_banned_content(user_message):
            return False, "부적절한 내용이 포함되어 있습니다. 다른 질문을 해주세요."
        
        # 와석초 관련 질문인지 판별
        if not self.is_school_related(user_message):
            return False, "와석초등학교 관련 질문에만 답변할 수 있습니다."
        
        # 1. 식단 관련 질문 확인 (우선순위 높음)
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
        
        # 3. 간단한 키워드 기반 답변 (우선순위 높음)
        simple_responses = {
            # 인사 관련
            "안녕": "안녕하세요! 와석초등학교 챗봇입니다. 무엇을 도와드릴까요?",
            "안녕하세요": "안녕하세요! 와석초등학교 챗봇입니다. 무엇을 도와드릴까요?",
            "안녕!": "안녕하세요! 와석초등학교 챗봇입니다. 무엇을 도와드릴까요?",
            "안녕~": "안녕하세요! 와석초등학교 챗봇입니다. 무엇을 도와드릴까요?",
            
            # 도움 요청 관련
            "도움": "와석초등학교 관련 질문에 답변해드립니다. 급식, 방과후, 상담, 전학 등에 대해 물어보세요.",
            "도움말": "와석초등학교 관련 질문에 답변해드립니다. 급식, 방과후, 상담, 전학 등에 대해 물어보세요.",
            "도움말이 필요해": "와석초등학교 관련 질문에 답변해드립니다. 급식, 방과후, 상담, 전학 등에 대해 물어보세요.",
            "도움이 필요해": "와석초등학교 관련 질문에 답변해드립니다. 급식, 방과후, 상담, 전학 등에 대해 물어보세요.",
            
            # 감사 관련
            "감사": "도움이 되어서 기쁩니다! 다른 질문이 있으시면 언제든 말씀해주세요.",
            "감사합니다": "도움이 되어서 기쁩니다! 다른 질문이 있으시면 언제든 말씀해주세요.",
            "고마워": "천만에요! 더 궁금한 점이 있으시면 언제든 물어보세요.",
            "고마워요": "천만에요! 더 궁금한 점이 있으시면 언제든 물어보세요.",
            "고맙습니다": "천만에요! 더 궁금한 점이 있으시면 언제든 물어보세요.",
            
            # 기타 일반적인 질문
            "뭐해": "와석초등학교 관련 질문에 답변하고 있어요. 무엇을 도와드릴까요?",
            "뭐하고 있어": "와석초등학교 관련 질문에 답변하고 있어요. 무엇을 도와드릴까요?",
            "뭐해?": "와석초등학교 관련 질문에 답변하고 있어요. 무엇을 도와드릴까요?",
            "뭐하고 있어?": "와석초등학교 관련 질문에 답변하고 있어요. 무엇을 도와드릴까요?",
            
            # 작별 인사
            "잘 있어": "안녕히 가세요! 또 궁금한 점이 있으시면 언제든 말씀해주세요.",
            "잘 있어요": "안녕히 가세요! 또 궁금한 점이 있으시면 언제든 말씀해주세요.",
            "잘 있어~": "안녕히 가세요! 또 궁금한 점이 있으시면 언제든 말씀해주세요.",
            "잘 있어요~": "안녕히 가세요! 또 궁금한 점이 있으시면 언제든 말씀해주세요."
        }
        
        # 부분 매칭으로 간단한 응답 찾기 (우선순위 높게 처리)
        for keyword, response in simple_responses.items():
            if keyword in user_message:
                self.db.save_conversation(user_id, user_message, response)
                return True, response
        
        # 4. QA 데이터베이스에서 유사한 질문 찾기
        qa_match = self.find_qa_match(user_message)
        if qa_match:
            response = qa_match['answer']
            
            # 이미지 첨부 응답 처리
            if "사진 첨부" in response or "이미지 파일 첨부" in response:
                response = self.add_image_to_response(response, qa_match)
            
            if qa_match.get('additional_answer'):
                response += f"\n\n추가 정보:\n{qa_match['additional_answer']}"
            
            self.db.save_conversation(user_id, user_message, response)
            return True, response
        
        # 5. OpenAI를 통한 응답 (마지막 수단, 타임아웃 방지를 위해 간단하게)
        try:
            # 간단한 프롬프트만 사용
            simple_prompt = f"와석초등학교 챗봇입니다. 다음 질문에 대해 간단하고 친근하게 답변해주세요: {user_message}"
            
            response = openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": simple_prompt}],
                temperature=0.7,
                max_tokens=100,  # 토큰 수 줄임
                top_p=1.0
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 응답이 너무 길면 자르기
            if len(ai_response) > 150:
                ai_response = ai_response[:150] + "..."
            
            self.db.save_conversation(user_id, user_message, ai_response)
            return True, ai_response
            
        except Exception as e:
            print(f"OpenAI 처리 중 오류: {e}")
            fallback_response = "죄송합니다. 해당 질문에 대한 답변을 찾을 수 없습니다. 다른 질문을 해주세요."
            self.db.save_conversation(user_id, user_message, fallback_response)
            return False, fallback_response
    
    def add_image_to_response(self, response: str, qa_match: Dict) -> str:
        """이미지 첨부 응답에 실제 이미지 URL 추가"""
        try:
            # 질문 카테고리에 따른 이미지 매핑
            image_mapping = {
                "학사일정": {
                    "url": "https://pajuwaseok-e.goepj.kr/pajuwaseok-e/na/ntt/selectNttInfo.do?mi=8416&bbsId=5770&nttSn=1256416",
                    "alt": "학사일정"
                },
                "교실 배치도": {
                    "url": "https://pajuwaseok-e.goepj.kr/pajuwaseok-e/na/ntt/selectNttInfo.do?mi=8416&bbsId=5770&nttSn=1256417",
                    "alt": "교실 배치도"
                },
                "정차대": {
                    "url": "https://pajuwaseok-e.goepj.kr/pajuwaseok-e/na/ntt/selectNttInfo.do?mi=8416&bbsId=5770&nttSn=1256418",
                    "alt": "정차대 안내"
                },
                "학교시설": {
                    "url": "https://pajuwaseok-e.goepj.kr/pajuwaseok-e/na/ntt/selectNttInfo.do?mi=8416&bbsId=5770&nttSn=1256419",
                    "alt": "학교시설 이용시간"
                }
            }
            
            # 질문 내용에 따른 이미지 선택
            question_lower = qa_match['question'].lower()
            
            if "학사일정" in response or "개학" in question_lower:
                image_info = image_mapping["학사일정"]
            elif "교실" in question_lower or "배치" in question_lower:
                image_info = image_mapping["교실 배치도"]
            elif "정차" in question_lower or "등하교" in question_lower:
                image_info = image_mapping["정차대"]
            elif "시설" in question_lower or "체육관" in question_lower:
                image_info = image_mapping["학교시설"]
            else:
                # 기본적으로 학사일정 이미지 사용
                image_info = image_mapping["학사일정"]
            
            # JSON 형태로 이미지 정보 포함
            image_response = {
                "text": response,
                "image": {
                    "url": image_info["url"],
                    "alt": image_info["alt"]
                }
            }
            
            return str(image_response)
            
        except Exception as e:
            print(f"이미지 첨부 처리 중 오류: {e}")
            return response 