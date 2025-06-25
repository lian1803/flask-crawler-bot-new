# AI 관련 코드 백업 파일
# 나중에 필요하면 이 코드를 app.py에 다시 추가할 수 있습니다.

from openai import OpenAI
import os

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

# 사용법:
# 1. 이 파일을 app.py에 import
# 2. handle_request 함수에서 AI 호출 부분을 다시 활성화
# 3. requirements.txt에 openai 라이브러리 다시 추가 