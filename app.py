from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime
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
            response = "최근 공지사항 5개입니다:\n\n"
            for title, created_at in results:
                response += f"• {title} ({created_at})\n"
            conn.close()
            return response
    
    conn.close()
    return None

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
        ai_answer = analyze_with_ai(user_message)
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
    # init_db()는 data_loader.py에서 처리
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 