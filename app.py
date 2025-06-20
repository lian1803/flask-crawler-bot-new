from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime
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

# 1단계: 직접 데이터 검색
def search_database(user_message):
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 식단 관련 질문
    meal_keywords = ['점심', '메뉴', '식단', '밥', '급식', '오늘', '내일', '어제']
    if any(keyword in user_message for keyword in meal_keywords):
        # 날짜 추출
        today = datetime.now().strftime('%Y-%m-%d')
        
        if '오늘' in user_message:
            date = today
        elif '내일' in user_message:
            # 내일 날짜 계산
            from datetime import timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            date = tomorrow.strftime('%Y-%m-%d')
        else:
            date = today
            
        cursor.execute('SELECT menu FROM meals WHERE date = ? AND meal_type = "중식"', (date,))
        result = cursor.fetchone()
        
        if result and result[0]:
            conn.close()
            return f"{date} 중식 메뉴:\n{result[0]}"
    
    # 공지사항 관련 질문
    notice_keywords = ['공지', '알림', '안내', '새소식', '뉴스']
    if any(keyword in user_message for keyword in notice_keywords):
        cursor.execute('SELECT title, created_at FROM notices ORDER BY created_at DESC LIMIT 5')
        results = cursor.fetchall()
        
        if results:
            response = "최근 공지사항:\n"
            for title, created_at in results:
                response += f"• {title} ({created_at})\n"
            conn.close()
            return response
    
    conn.close()
    return None

# 2단계: AI 분석 (간단한 키워드 매칭)
def analyze_with_ai(user_message, crawled_data):
    # 식단 관련 질문에 대한 일반적인 답변
    if '식단' in user_message or '메뉴' in user_message:
        return "식단 정보는 매일 업데이트됩니다. 구체적인 날짜를 말씀해주시면 더 정확한 정보를 제공해드릴 수 있습니다."
    
    # 공지사항 관련 질문
    if '공지' in user_message or '알림' in user_message:
        return "공지사항은 학교 홈페이지에서 실시간으로 업데이트됩니다. 최신 정보를 확인해보세요."
    
    # 학교 관련 일반 질문
    school_keywords = ['학교', '등교', '하교', '수업', '시험']
    if any(keyword in user_message for keyword in school_keywords):
        return "학교 관련 문의사항은 학교로 직접 연락하시는 것이 가장 정확합니다."
    
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

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        user_message = data['userRequest']['utterance']
        
        print(f"사용자 메시지: {user_message}")
        
        # 1단계: 직접 검색
        direct_answer = search_database(user_message)
        if direct_answer:
            print(f"1단계 답변: {direct_answer}")
            return jsonify(create_kakao_response(direct_answer))
        
        # 2단계: AI 분석
        ai_answer = analyze_with_ai(user_message, None)
        if ai_answer:
            print(f"2단계 답변: {ai_answer}")
            return jsonify(create_kakao_response(ai_answer))
        
        # 3단계: 학교 문의 안내
        fallback_message = "죄송합니다. 해당 정보를 찾을 수 없습니다. 학교쪽으로 문의주세요."
        print(f"3단계 답변: {fallback_message}")
        return jsonify(create_kakao_response(fallback_message))
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return jsonify(create_kakao_response("시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."))

@app.route('/')
def home():
    return "파주와석초등학교 챗봇 서버가 실행 중입니다!"

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 