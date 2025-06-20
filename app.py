from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
import re
from openai import OpenAI

app = Flask(__name__)

# --- OpenAI 클라이언트 설정 ---
# Render.com의 환경 변수에서 API 키를 가져옵니다.
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    print("경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    # 로컬 테스트용 임시 키 (실제 배포 시에는 비워두거나 삭제)
    # api_key = "YOUR_FALLBACK_API_KEY_HERE" 

client = OpenAI(api_key=api_key)

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

# DB에서 모든 데이터 가져오기 (AI에게 컨텍스트로 제공)
def get_all_data_for_ai():
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 최근 식단 10개
    cursor.execute('SELECT date, menu FROM meals ORDER BY date DESC LIMIT 10')
    meals = cursor.fetchall()
    
    # 최근 공지사항 10개
    cursor.execute('SELECT title, created_at, content FROM notices ORDER BY created_at DESC LIMIT 10')
    notices = cursor.fetchall()
    
    conn.close()
    
    context = "### 파주와석초등학교 정보 ###\n\n"
    context += "--- 최신 식단 (10개) ---\n"
    for date, menu in meals:
        context += f"날짜: {date}\n메뉴: {menu}\n\n"
        
    context += "\n--- 최신 공지사항 (10개) ---\n"
    for title, created_at, content in notices:
        context += f"날짜: {created_at}\n제목: {title}\n내용: {content[:100]}...\n\n" # 내용은 100자만
        
    return context

# 2단계: AI 분석 (비용 최적화)
def analyze_with_ai(user_message):
    try:
        # 1. AI에게 전달할 전체 데이터 컨텍스트 가져오기
        data_context = get_all_data_for_ai()
        
        # 2. AI에게 역할과 지침 부여 (System Prompt)
        system_prompt = f"""
        당신은 파주와석초등학교의 친절한 안내 챗봇입니다.
        아래에 제공되는 실제 학교 데이터를 기반으로만 답변해야 합니다.
        데이터에 없는 내용은 절대로 지어내지 말고, "해당 정보는 아직 없어요. 학교에 직접 문의해주세요." 라고 솔직하게 답변하세요.
        답변은 항상 한국어로, 완전한 문장으로 부드럽게 만들어주세요.

        --- 제공된 데이터 ---
        {data_context}
        --------------------
        """
        
        # 3. OpenAI API 호출
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7, # 너무 딱딱하지 않게
        )
        
        answer = completion.choices[0].message.content
        return answer

    except Exception as e:
        print(f"OpenAI API 오류: {str(e)}")
        return None

# 카카오톡 응답 생성
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

# --- 메인 핸들러 ---
def handle_request(user_message):
    """사용자 요청을 단계별로 처리합니다."""
    
    # 1단계: 식단 관련 질문 처리 (날짜 인식)
    meal_keywords = ['급식', '식단', '메뉴', '밥', '점심']
    if any(keyword in user_message for keyword in meal_keywords):
        target_date = get_target_date(user_message)
        if target_date:
            print(f"INFO: 식단 질문으로 판단, 날짜: {target_date}")
            return get_meal_info(target_date)

    # 2단계: 공지사항 관련 질문 처리
    notice_keywords = ['공지', '알림', '안내', '새소식']
    if any(keyword in user_message for keyword in notice_keywords):
        print("INFO: 공지사항 질문으로 판단")
        return get_latest_notices()
        
    # 3단계: 1, 2단계에 해당하지 않으면 AI에게 질문
    print("INFO: 일반 질문으로 판단, AI 호출")
    ai_answer = analyze_with_ai(user_message)
    if ai_answer:
        return ai_answer
        
    # 4단계: AI도 실패하면 최종 폴백 메시지
    return "죄송합니다. 요청을 이해하지 못했습니다. 학교로 직접 문의해주세요."

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        user_message = data['userRequest']['utterance']
        
        # 새로운 핸들러 호출
        response_text = handle_request(user_message)
        
        print(f"사용자: '{user_message}' / 챗봇: '{response_text[:30]}...'")
        return jsonify(create_kakao_response(response_text))
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        # 사용자에게는 간단한 오류 메시지 표시
        return jsonify(create_kakao_response("시스템에 오류가 발생하여 요청을 처리할 수 없습니다."))

@app.route('/')
def home():
    return "파주와석초등학교 챗봇 서버 v2.0 (AI-Powered)"

if __name__ == '__main__':
    # init_db()는 data_loader.py에서 처리
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 