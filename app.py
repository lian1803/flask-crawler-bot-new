from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
import re
from openai import OpenAI

app = Flask(__name__)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 공지사항 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT,
            created_at TEXT,
            tags TEXT,
            category TEXT
        )
    ''')
    
    # 식단 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            meal_type TEXT,
            menu TEXT,
            image_url TEXT
        )
    ''')
    
    # QA 데이터 테이블 (이미 생성되어 있음)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qa_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            additional_answer TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_target_date(text):
    """사용자 메시지에서 날짜를 추출합니다."""
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
        # 올해 날짜로 가정
        return today.replace(month=month, day=day).strftime("%Y-%m-%d")
        
    return None

def get_meal_info(date):
    """특정 날짜의 식단 정보를 DB에서 가져옵니다."""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT menu FROM meals WHERE date = ? AND meal_type = "중식"', (date,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        return f"{date} 중식 메뉴입니다:\n\n{result[0]}"
    return f"{date}에는 식단 정보가 없습니다."

def get_latest_notices():
    """최신 공지사항 5개를 DB에서 가져옵니다."""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT title, created_at FROM notices ORDER BY created_at DESC LIMIT 5')
    results = cursor.fetchall()
    conn.close()
    if results:
        response = "최근 공지사항 5개입니다:\n\n"
        for title, created_at in results:
            response += f"• {title} ({created_at})\n"
        return response
    return "현재 등록된 공지사항이 없습니다."

def find_qa_match(user_message):
    """qa_data 테이블에서 사용자 질문과 가장 유사한 답변을 찾습니다."""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 모든 QA 데이터 가져오기
    cursor.execute('SELECT question, answer, additional_answer FROM qa_data')
    qa_data = cursor.fetchall()
    conn.close()
    
    best_match = None
    best_score = 0
    
    for question, answer, additional_answer in qa_data:
        # 키워드 매칭 점수 계산
        score = 0
        user_words = set(user_message.lower().split())
        qa_words = set(question.lower().split())
        
        # 공통 단어 수 계산
        common_words = user_words.intersection(qa_words)
        score = len(common_words)
        
        # 특정 키워드에 가중치 부여
        important_keywords = ['학년', '끝나', '방과후', '시정표', '급식', '공지', '일정']
        for keyword in important_keywords:
            if keyword in user_message and keyword in question:
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = (question, answer, additional_answer)
    
    # 최소 점수 이상일 때만 매칭 성공으로 간주
    if best_score >= 1:
        return best_match
    return None

def search_detailed_info(keyword):
    """키워드를 기반으로 notices 테이블에서 구체적인 정보를 검색합니다."""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 키워드로 공지사항 검색
    cursor.execute('''
        SELECT title, content FROM notices 
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY created_at DESC LIMIT 3
    ''', (f'%{keyword}%', f'%{keyword}%'))
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        detailed_info = f"관련 상세 정보를 찾았습니다:\n\n"
        for title, content in results:
            detailed_info += f"📋 {title}\n"
            if content:
                # 내용이 너무 길면 앞부분만 표시
                content_preview = content[:200] + "..." if len(content) > 200 else content
                detailed_info += f"{content_preview}\n"
            detailed_info += "\n"
        return detailed_info
    return None

# --- OpenAI 클라이언트 설정 ---
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
client = OpenAI(api_key=api_key)

def get_all_data_for_ai():
    """DB에서 모든 데이터 가져오기 (AI에게 컨텍스트로 제공)"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    # 최근 식단 5개
    cursor.execute('SELECT date, menu FROM meals ORDER BY date DESC LIMIT 5')
    meals = cursor.fetchall()
    # 최근 공지사항 5개
    cursor.execute('SELECT title, created_at, content FROM notices ORDER BY created_at DESC LIMIT 5')
    notices = cursor.fetchall()
    conn.close()
    context = "### 파주와석초등학교 정보 ###\n\n"
    context += "--- 최신 식단 (5개) ---\n"
    for date, menu in meals:
        context += f"날짜: {date}\n메뉴: {menu}\n\n"
    context += "\n--- 최신 공지사항 (5개) ---\n"
    for title, created_at, content in notices:
        context += f"날짜: {created_at}\n제목: {title}\n내용: {content[:100]}...\n\n" # 내용은 100자만
    return context

def analyze_with_ai(user_message):
    """2단계: AI 분석 (비용 최적화)"""
    try:
        data_context = get_all_data_for_ai()
        system_prompt = f"""
        당신은 파주와석초등학교의 친절한 안내 챗봇입니다.
        아래에 제공되는 실제 학교 데이터를 기반으로만 답변해야 합니다.
        데이터에 없는 내용은 절대로 지어내지 말고, \"해당 정보는 아직 없어요. 학교에 직접 문의해주세요.\" 라고 솔직하게 답변하세요.
        답변은 항상 한국어로, 완전한 문장으로 부드럽게 만들어주세요.
        --- 제공된 데이터 ---
        {data_context}
        --------------------
        """
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )
        answer = completion.choices[0].message.content
        return answer
    except Exception as e:
        print(f"OpenAI API 오류: {str(e)}")
        return None

def extract_url(text):
    """텍스트에서 URL 추출"""
    if not text:
        return None
    url_pattern = r'(https?://[\w\-\.\?&=/%#]+)'
    match = re.search(url_pattern, text)
    if match:
        return match.group(1)
    return None

# --- 개선된 메인 핸들러 ---
def handle_request(user_message):
    """사용자 요청을 단계별로 처리합니다. (맥락 이해 개선 + 자연스러운 링크 안내)"""
    
    # 1단계: 식단 관련 질문 처리
    meal_keywords = ['급식', '식단', '메뉴', '밥', '점심']
    if any(keyword in user_message for keyword in meal_keywords):
        target_date = get_target_date(user_message)
        if target_date:
            print(f"INFO: 식단 질문으로 판단, 날짜: {target_date}")
            meal_answer = get_meal_info(target_date)
            if '없습니다' not in meal_answer:
                return meal_answer
    
    # 2단계: 공지사항 관련 질문 처리
    notice_keywords = ['공지', '알림', '안내', '새소식']
    if any(keyword in user_message for keyword in notice_keywords):
        print("INFO: 공지사항 질문으로 판단")
        notice_answer = get_latest_notices()
        if '없습니다' not in notice_answer:
            return notice_answer
    
    # 3단계: QA 데이터에서 맥락 매칭
    print("INFO: QA 데이터에서 맥락 매칭 시도")
    qa_match = find_qa_match(user_message)
    
    if qa_match:
        question, answer, additional_answer = qa_match
        print(f"INFO: QA 매칭 성공 - {question}")
        
        # 4단계: QA 답변을 키워드로 사용해서 구체적인 정보 검색
        detailed_info = search_detailed_info(answer)
        
        # --- 자연스러운 링크 안내 추가 ---
        url = extract_url(answer) or extract_url(additional_answer)
        if url:
            response = "관련 내용은 아래 링크에서 확인하실 수 있습니다!\n" + url
            return response
        # ---
        if detailed_info:
            response = detailed_info
            if additional_answer:
                response += f"\n💡 추가 정보: {additional_answer}"
            return response
        else:
            response = answer
            if additional_answer:
                response += f"\n\n추가 정보: {additional_answer}"
            return response
    
    # 5단계: AI에게 넘기기
    print("INFO: AI에게 질문 전달")
    ai_answer = analyze_with_ai(user_message)
    if ai_answer:
        return ai_answer
    
    # 6단계: 최종 폴백
    return "죄송합니다. 해당 정보를 찾을 수 없습니다. 학교쪽으로 문의해주세요."

def create_kakao_response(message):
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": message
                    }
                }
            ]
        }
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        user_message = data['userRequest']['utterance']
        
        # 새로운 핸들러 호출 (맥락 이해 개선)
        response_text = handle_request(user_message)
        
        print(f"사용자: '{user_message}' / 챗봇: '{response_text[:30]}...'")
        return jsonify(create_kakao_response(response_text))
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        # 사용자에게는 간단한 오류 메시지 표시
        return jsonify(create_kakao_response("시스템에 오류가 발생하여 요청을 처리할 수 없습니다."))

@app.route('/')
def home():
    return "파주와석초등학교 챗봇 서버 v2.2 (맥락 이해 개선)"

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 