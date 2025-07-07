import json
import openai
import requests
from datetime import datetime
from transformers import GPT2Tokenizer
from config import openai_model, temperature, max_tokens, bot_name
from database import SchoolDatabase
from utils import (
    is_meal_related, is_notice_related, is_greeting, 
    extract_date_from_text, format_meal_info, format_notice_info
)

# GPT2 토크나이저 초기화
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

class SchoolBotLogic:
    def __init__(self):
        self.db = SchoolDatabase()
        self.conversations = {}
        self.max_conversation_length = 10
        
        # OpenAI 설정
        openai.api_key = openai.api_key
        
    def count_tokens(self, text):
        """텍스트의 토큰 수를 계산합니다."""
        return len(tokenizer.encode(text, truncation=True))
    
    def load_conversation_history(self, user_id):
        """사용자의 대화 히스토리를 로드합니다."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def save_conversation(self, user_id, user_message, bot_response):
        """대화를 저장합니다."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # 대화 히스토리 길이 제한
        if len(self.conversations[user_id]) > self.max_conversation_length:
            self.conversations[user_id] = self.conversations[user_id][-self.max_conversation_length:]
    
    def read_prompt(self):
        """프롬프트 파일을 읽습니다."""
        try:
            with open("logic/prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "당신은 파주와석초등학교의 친근하고 도움이 되는 챗봇입니다."
    
    def create_system_message(self, user_id):
        """시스템 메시지를 생성합니다."""
        prompt = self.read_prompt()
        
        # 학교 데이터베이스 정보 추가
        qa_data = self.db.get_all_qa_data()
        if qa_data:
            qa_context = "\n\n## 학교 QA 데이터베이스:\n"
            for qa in qa_data[:10]:  # 최대 10개만 포함
                qa_context += f"Q: {qa['question']}\nA: {qa['answer']}\n\n"
            prompt += qa_context
        
        return prompt
    
    def handle_meal_request(self, user_message):
        """급식 관련 요청을 처리합니다."""
        date = extract_date_from_text(user_message)
        meal_info = self.db.get_meal_info(date)
        return format_meal_info(meal_info)
    
    def handle_notice_request(self, user_message):
        """공지사항 관련 요청을 처리합니다."""
        notices = self.db.get_latest_notices(5)
        return format_notice_info(notices)
    
    def handle_qa_request(self, user_message):
        """QA 데이터베이스에서 답변을 찾습니다."""
        # 정확한 매칭 시도
        qa_result = self.db.search_qa_data(user_message)
        if qa_result:
            answer = qa_result["answer"]
            if qa_result.get("additional_answer"):
                answer += f"\n\n{qa_result['additional_answer']}"
            return answer
        
        # 키워드 검색 시도
        keywords = self.extract_keywords(user_message)
        for keyword in keywords:
            qa_results = self.db.search_qa_by_keyword(keyword, 3)
            if qa_results:
                # 가장 관련성 높은 답변 선택
                return qa_results[0]["answer"]
        
        return None
    
    def extract_keywords(self, text):
        """텍스트에서 키워드를 추출합니다."""
        # 간단한 키워드 추출 (한글 단어, 2글자 이상)
        import re
        keywords = re.findall(r'[가-힣]{2,}', text)
        return keywords[:5]  # 최대 5개 키워드
    
    def generate_ai_response(self, user_message, user_id):
        """AI를 사용하여 답변을 생성합니다."""
        try:
            # 대화 히스토리 로드
            conversation_history = self.load_conversation_history(user_id)
            
            # 시스템 메시지 생성
            system_message = self.create_system_message(user_id)
            
            # 메시지 구성
            messages = [{"role": "system", "content": system_message}]
            
            # 대화 히스토리 추가
            for conv in conversation_history[-6:]:  # 최근 6개 대화만 포함
                messages.append({"role": "user", "content": conv["user"]})
                messages.append({"role": "assistant", "content": conv["bot"]})
            
            # 현재 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})
            
            # 토큰 수 확인 및 조정
            total_tokens = sum(self.count_tokens(msg["content"]) for msg in messages)
            if total_tokens > 3000:  # 토큰 제한
                # 가장 오래된 메시지들 제거
                while total_tokens > 3000 and len(messages) > 3:
                    removed_tokens = self.count_tokens(messages[1]["content"]) + self.count_tokens(messages[2]["content"])
                    messages.pop(1)  # user message
                    messages.pop(1)  # assistant message
                    total_tokens -= removed_tokens
            
            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model=openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI 응답 생성 중 오류: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    def process_message(self, user_message, user_id):
        """사용자 메시지를 처리하고 적절한 답변을 생성합니다."""
        print(f"사용자 {user_id}: {user_message}")
        
        # 1. 인사말 처리
        if is_greeting(user_message):
            response = f"안녕하세요! {bot_name}입니다. 😊\n\n무엇을 도와드릴까요?\n\n• 오늘 급식 메뉴\n• 최신 공지사항\n• 학교 관련 질문"
            self.save_conversation(user_id, user_message, response)
            return response
        
        # 2. 급식 관련 요청 처리
        if is_meal_related(user_message):
            response = self.handle_meal_request(user_message)
            self.save_conversation(user_id, user_message, response)
            return response
        
        # 3. 공지사항 관련 요청 처리
        if is_notice_related(user_message):
            response = self.handle_notice_request(user_message)
            self.save_conversation(user_id, user_message, response)
            return response
        
        # 4. QA 데이터베이스에서 답변 찾기
        qa_response = self.handle_qa_request(user_message)
        if qa_response:
            self.save_conversation(user_id, user_message, qa_response)
            return qa_response
        
        # 5. AI를 사용한 답변 생성
        ai_response = self.generate_ai_response(user_message, user_id)
        self.save_conversation(user_id, user_message, ai_response)
        return ai_response
    
    def get_conversation_summary(self, user_id):
        """사용자의 대화 요약을 제공합니다."""
        if user_id not in self.conversations:
            return "대화 기록이 없습니다."
        
        conversations = self.conversations[user_id]
        if not conversations:
            return "대화 기록이 없습니다."
        
        summary = f"📝 최근 대화 기록 ({len(conversations)}개)\n\n"
        for i, conv in enumerate(conversations[-5:], 1):  # 최근 5개만
            summary += f"{i}. Q: {conv['user'][:30]}...\n"
            summary += f"   A: {conv['bot'][:50]}...\n\n"
        
        return summary 