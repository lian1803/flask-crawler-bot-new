from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
import re

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

# --- 메인 핸들러 (AI 제거 버전) ---
def handle_request(user_message):
    """사용자 요청을 단계별로 처리합니다. (AI 제거 버전)"""
    
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
        
    # 3단계: 1,2단계에 해당하지 않으면 기본 답변 (AI 제거)
    print("INFO: 일반 질문으로 판단, 기본 답변")
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
        
        # 새로운 핸들러 호출 (AI 제거 버전)
        response_text = handle_request(user_message)
        
        print(f"사용자: '{user_message}' / 챗봇: '{response_text[:30]}...'")
        return jsonify(create_kakao_response(response_text))
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        # 사용자에게는 간단한 오류 메시지 표시
        return jsonify(create_kakao_response("시스템에 오류가 발생하여 요청을 처리할 수 없습니다."))

@app.route('/')
def home():
    return "파주와석초등학교 챗봇 서버 v2.1 (Fast Response - No AI)"

if __name__ == '__main__':
    init_db()  # 서버 시작 시 DB 초기화
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 