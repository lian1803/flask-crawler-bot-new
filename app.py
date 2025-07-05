from flask import Flask, request, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
import re
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)

# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.start()

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

def auto_update_excel_data():
    """매일 자정에 실행되는 엑셀 데이터 자동 업데이트 함수"""
    try:
        print(f"[{datetime.now()}] 엑셀 데이터 자동 업데이트 시작")
        
        excel_file = '와석초 카카오톡 챗봇 개발을 위한 질문과 답변(0702).xlsx'
        
        # 엑셀 파일 존재 확인
        if not os.path.exists(excel_file):
            print(f"[{datetime.now()}] 엑셀 파일을 찾을 수 없습니다: {excel_file}")
            return
        
        # 데이터베이스 연결
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        
        total_added = 0
        
        xl = pd.ExcelFile(excel_file)
        for sheet_name in xl.sheet_names:
            print(f"[{datetime.now()}] {sheet_name} 시트 처리 중")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            if sheet_name in ['초등', '유치원']:
                for index, row in df.iterrows():
                    question = row.get('질문 예시', None)
                    answer = row.get('답변 ', None)
                    additional_answer = row.get('추가답변', '')
                    if pd.isna(additional_answer):
                        additional_answer = ''
                    if pd.notna(question) and pd.notna(answer):
                        cursor.execute("SELECT id FROM qa_data WHERE question = ? AND category = ?", (question, sheet_name))
                        existing = cursor.fetchone()
                        if not existing:
                            cursor.execute(
                                "INSERT INTO qa_data (question, answer, additional_answer, category) VALUES (?, ?, ?, ?)",
                                (question, answer, additional_answer, sheet_name)
                            )
                            total_added += 1
                            print(f"[{datetime.now()}] 추가됨: {question[:30]}...")
                        else:
                            print(f"[{datetime.now()}] 중복됨: {question[:30]}...")
            else:
                # 첨부 사진 파일 시트 등 기타 시트 처리
                for index, row in df.iterrows():
                    # 첫 컬럼을 질문, 두 번째 컬럼을 답변, 나머지는 추가답변으로 합침
                    columns = df.columns.tolist()
                    question = row.get(columns[0], None)
                    answer = row.get(columns[1], None) if len(columns) > 1 else ''
                    additional_answer = ''
                    if len(columns) > 2:
                        additional_parts = [str(row.get(col, '')) for col in columns[2:] if pd.notna(row.get(col, ''))]
                        additional_answer = '\n'.join(additional_parts)
                    if pd.notna(question) and pd.notna(answer):
                        cursor.execute("SELECT id FROM qa_data WHERE question = ? AND category = ?", (str(question), sheet_name))
                        existing = cursor.fetchone()
                        if not existing:
                            cursor.execute(
                                "INSERT INTO qa_data (question, answer, additional_answer, category) VALUES (?, ?, ?, ?)",
                                (str(question), str(answer), additional_answer, sheet_name)
                            )
                            total_added += 1
                            print(f"[{datetime.now()}] 추가됨: {str(question)[:30]}...")
                        else:
                            print(f"[{datetime.now()}] 중복됨: {str(question)[:30]}...")
        
        # 변경사항 저장
        conn.commit()
        conn.close()
        
        print(f"[{datetime.now()}] 엑셀 데이터 자동 업데이트 완료 - 총 {total_added}개 추가됨")
        
    except Exception as e:
        print(f"[{datetime.now()}] 엑셀 데이터 자동 업데이트 중 오류 발생: {str(e)}")

# 스케줄러에 작업 추가 (매일 자정에 실행)
scheduler.add_job(
    func=auto_update_excel_data,
    trigger=CronTrigger(hour=0, minute=0),  # 매일 자정 (00:00)
    id='auto_update_excel_data',
    name='엑셀 데이터 자동 업데이트',
    replace_existing=True
)

# 테스트용: 1분마다 실행 (개발/테스트 시에만 사용)
# scheduler.add_job(
#     func=auto_update_excel_data,
#     trigger='interval',
#     minutes=1,
#     id='test_auto_update_excel_data',
#     name='테스트용 엑셀 데이터 자동 업데이트',
#     replace_existing=True
# )

print(f"[{datetime.now()}] 스케줄러가 시작되었습니다. 매일 자정에 엑셀 데이터가 자동으로 업데이트됩니다.")

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

def get_meal_info(date=None):
    """특정 날짜의 식단 정보를 DB에서 가져옵니다. date가 없으면 오늘 날짜 사용."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.strptime(date, "%Y-%m-%d").weekday()  # 0=월, ..., 5=토, 6=일
    if weekday >= 5:
        return f"{date}는 주말(토/일)이라 급식이 없습니다."
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

def classify_question_category(user_message):
    """사용자 질문을 분석하여 카테고리(초등/유치원/첨부사진)를 분류합니다."""
    user_message_lower = user_message.lower()
    
    # 초등학교 관련 키워드
    elementary_keywords = [
        '초등', '초등학교', '학년', '교과서', '방과후', '급식', '학사일정', 
        '전입', '전출', '결석', '체험학습', '학교장', '담임', '선생님',
        '학생', '교실', '반', '수업', '하교', '등교', '버스', '늘봄',
        '돌봄', '방과후학교', '학교폭력', '재학증명서', '생활기록부'
    ]
    
    # 유치원 관련 키워드
    kindergarten_keywords = [
        '유치원', '유아', '하원', '원장', '교사', '면담', '교육비',
        '수담금', '학비', '특수학급', '현장학습', '특성화', '학부모',
        '참여수업', '유치원복', '주정차', '학원선생님', '대기자',
        '유아모집', '입학설명회', '예비소집'
    ]
    
    # 첨부사진 관련 키워드
    attachment_keywords = [
        '사진', '파일', '첨부', '양식', '서류', '신고서', '보고서',
        '신청서', '확인서', '증명서', '계획서', '시간표', '일정표'
    ]
    
    # 점수 계산
    elementary_score = sum(1 for keyword in elementary_keywords if keyword in user_message_lower)
    kindergarten_score = sum(1 for keyword in kindergarten_keywords if keyword in user_message_lower)
    attachment_score = sum(1 for keyword in attachment_keywords if keyword in user_message_lower)
    
    # 가장 높은 점수의 카테고리 반환
    scores = {
        '초등': elementary_score,
        '유치원': kindergarten_score,
        '첨부 사진 파일': attachment_score
    }
    
    max_score = max(scores.values())
    if max_score > 0:
        # 가장 높은 점수의 카테고리들 중에서 선택
        max_categories = [cat for cat, score in scores.items() if score == max_score]
        return max_categories[0]  # 첫 번째 카테고리 반환
    
    return None  # 분류 불가능

def normalize_text(text):
    """텍스트를 정규화합니다 (동의어 처리 포함)"""
    if not text:
        return ""
    
    text_lower = text.lower()
    
    # 동의어 사전
    synonyms = {
        "방과후": ["방과후학교", "방과후 과정", "방과후 프로그램"],
        "급식": ["식단", "메뉴", "밥", "점심", "중식"],
        "학사일정": ["시정표", "일정", "학사", "학사일정표"],
        "교과서": ["교과서", "교재", "책"],
        "담임": ["담임선생님", "담임교사", "담임"],
        "전입": ["전학", "전입", "입학"],
        "전출": ["전학", "전출", "졸업"],
        "결석": ["결석", "휴가", "병가"],
        "체험학습": ["체험학습", "현장학습", "견학"],
        "재학증명서": ["재학증명서", "재학증명", "증명서"],
        "생활기록부": ["생활기록부", "생활기록", "기록부"]
    }
    
    # 동의어 변환
    normalized_text = text_lower
    for main_word, synonym_list in synonyms.items():
        for synonym in synonym_list:
            if synonym in normalized_text:
                normalized_text = normalized_text.replace(synonym, main_word)
    
    return normalized_text

def analyze_intent(user_message):
    """사용자 질문의 의도를 분석합니다"""
    normalized_message = normalize_text(user_message)
    
    # 의도별 키워드
    intent_keywords = {
        "시간_문의": ["언제", "몇시", "시간", "끝나", "시작", "개학", "방학", "하교", "등교"],
        "장소_문의": ["어디", "위치", "장소", "보관함", "교실", "반", "행정실"],
        "절차_문의": ["어떻게", "절차", "신청", "발급", "연락", "상담", "신고"],
        "정보_문의": ["뭐", "무엇", "얼마", "몇", "정보", "알고", "궁금"]
    }
    
    intent_scores = {}
    for intent, keywords in intent_keywords.items():
        score = sum(1 for keyword in keywords if keyword in normalized_message)
        intent_scores[intent] = score
    
    # 가장 높은 점수의 의도 반환
    if intent_scores:
        max_intent = max(intent_scores, key=intent_scores.get)
        if intent_scores[max_intent] > 0:
            return max_intent
    
    return "일반_문의"

def calculate_answer_relevance(question, answer, user_intent):
    """답변의 관련성을 계산합니다"""
    relevance_score = 0
    
    # 의도별 가중치
    intent_weights = {
        "시간_문의": 5,
        "장소_문의": 4, 
        "절차_문의": 3,
        "정보_문의": 2,
        "일반_문의": 1
    }
    
    # 기본 점수
    relevance_score += intent_weights.get(user_intent, 1)
    
    # 답변의 구체성 점수
    if any(word in answer for word in ["시", "분", "일", "월", "년"]):
        relevance_score += 2  # 시간 정보가 있으면 +2
    if any(word in answer for word in ["위치", "장소", "어디", "교실", "반"]):
        relevance_score += 2  # 장소 정보가 있으면 +2
    if any(word in answer for word in ["절차", "신청", "발급", "연락"]):
        relevance_score += 2  # 절차 정보가 있으면 +2
    if "링크" in answer or "http" in answer:
        relevance_score += 1  # 링크가 있으면 +1
    
    return relevance_score

def find_qa_match_smart(user_message, preferred_category=None):
    """똑똑한 QA 매칭 (동의어 처리 + 의도 분석 + 관련성 점수)"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 모든 QA 데이터 가져오기
    cursor.execute('SELECT question, answer, additional_answer, category FROM qa_data')
    qa_data = cursor.fetchall()
    conn.close()
    
    # 사용자 의도 분석
    user_intent = analyze_intent(user_message)
    normalized_user_message = normalize_text(user_message)
    
    best_match = None
    best_score = 0
    
    for question, answer, additional_answer, category in qa_data:
        score = 0
        
        # 1. 정규화된 텍스트로 키워드 매칭
        normalized_question = normalize_text(question)
        user_words = set(normalized_user_message.split())
        qa_words = set(normalized_question.split())
        
        # 공통 단어 수 계산
        common_words = user_words.intersection(qa_words)
        score += len(common_words) * 2  # 가중치 증가
        
        # 2. 중요 키워드 매칭 (가중치 부여)
        important_keywords = ['학년', '끝나', '방과후', '시정표', '급식', '공지', '일정', '시간', '어디', '언제', '어떻게']
        for keyword in important_keywords:
            if keyword in normalized_user_message and keyword in normalized_question:
                score += 3
        
        # 3. 선호 카테고리 가중치
        if preferred_category and category == preferred_category:
            score += 3
        
        # 4. 답변 관련성 점수
        relevance_score = calculate_answer_relevance(question, answer, user_intent)
        score += relevance_score
        
        # 5. 정확한 매칭 보너스
        if any(word in normalized_user_message for word in normalized_question.split()):
            score += 5
        
        if score > best_score:
            best_score = score
            best_match = (question, answer, additional_answer, category, score)
    
    # 최소 점수 이상일 때만 매칭 성공으로 간주
    if best_score >= 3:  # 임계값 상향 조정
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
    """DB 정보만 사용, 학부모 안내 톤으로 답변하도록 프롬프트 강화"""
    try:
        data_context = get_all_data_for_ai()
        system_prompt = f"""
        당신은 파주와석초등학교의 챗봇입니다.
        아래에 제공되는 실제 학교 DB(엑셀) 정보만을 사용해서, 반드시 학부모님께 안내하듯 답변하세요.
        DB에 없는 내용은 절대로 지어내지 말고, '해당 정보는 학교로 문의해 주세요.'라고 답변하세요.
        답변은 항상 학부모님께 안내하는 말투로, 친절하고 공손하게 작성하세요.
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
            temperature=0.2,
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

def is_greeting_or_smalltalk(user_message):
    """인사/잡담 여부 판별"""
    greetings = [
        '안녕', '안녕하세요', '반가워', 'ㅎㅇ', 'hello', 'hi', '하이', '고마워', '감사', '수고', '잘 부탁', '헬로', '굿모닝', '굿밤', '잘자', '잘 지내', '좋은 하루', '좋은 아침', '수고하세요', '수고하셨습니다'
    ]
    msg = user_message.lower().replace(' ', '')
    return any(greet in msg for greet in greetings)

def get_exact_match_from_db(user_message):
    """DB에서 질문이 완전히 일치하는 답변을 찾음"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT answer, additional_answer FROM qa_data WHERE question = ?', (user_message,))
    result = cursor.fetchone()
    conn.close()
    if result:
        answer, additional_answer = result
        if additional_answer:
            return f"{answer}\n\n추가 정보: {additional_answer}"
        return answer
    return None

def find_link_answer_by_keyword(user_message):
    """질문에 포함된 주요 키워드가 들어간 DB 질문을 찾아, 링크가 있으면 안내"""
    keywords = [w for w in user_message.replace('?', '').replace('!', '').split() if len(w) > 1]
    if not keywords:
        return None
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    # 부분일치 검색 (질문에 키워드가 포함된 qa_data)
    for keyword in keywords:
        cursor.execute('SELECT answer, additional_answer FROM qa_data WHERE question LIKE ?', (f'%{keyword}%',))
        for answer, additional_answer in cursor.fetchall():
            url = extract_url(answer) or extract_url(additional_answer)
            if url:
                conn.close()
                return f"관련 안내는 아래 링크에서 확인하실 수 있습니다!\n{url}"
    conn.close()
    return None

# 불용어 리스트(확장 가능)
STOPWORDS = set(['우리', '저희', '애들', '정보', '학교', '문의', '관련', '있나요', '있을까요', '알려줘', '알려주세요', '좀', '어떻게', '무엇', '뭐', '어디', '언제', '누구', '왜', '몇', '가요', '인가요', '요'])

def extract_nouns(text):
    # konlpy 없이 한글/영문 단어만 추출 (2글자 이상, 불용어 제거)
    words = re.findall(r'[가-힣a-zA-Z]{2,}', text)
    return [w for w in words if w not in STOPWORDS]

def append_link_to_answer(answer, additional_answer):
    """답변/추가답변에 링크가 있으면 답변 마지막에 항상 링크를 동봉"""
    url = extract_url(answer) or extract_url(additional_answer)
    if url:
        return f"{answer}\n\n관련 자료는 아래 링크에서 확인하실 수 있습니다!\n{url}"
    return answer

def find_best_link_answer(user_message, sim_threshold=0.5):
    user_nouns = extract_nouns(user_message)
    if not user_nouns:
        return None
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT question, answer, additional_answer FROM qa_data')
    qa_rows = cursor.fetchall()
    conn.close()
    candidates = []
    for q, a, add in qa_rows:
        q_nouns = extract_nouns(q)
        if any(n in q_nouns for n in user_nouns):
            candidates.append((q, a, add))
    # 1. 후보가 여러 개면 유사도 기반으로 가장 가까운 질문의 답변 안내
    if candidates:
        questions = [q for q, _, _ in candidates]
        user_texts = [user_message] + questions
        vectorizer = TfidfVectorizer().fit(user_texts)
        user_vec = vectorizer.transform([user_message])
        qa_vecs = vectorizer.transform(questions)
        sims = cosine_similarity(user_vec, qa_vecs)[0]
        best_idx = sims.argmax()
        best_score = sims[best_idx]
        if best_score < sim_threshold:
            return None
        best_q, best_a, best_add = candidates[best_idx]
        answer_with_link = append_link_to_answer(best_a, best_add)
        if best_add and not extract_url(best_a) and not extract_url(best_add):
            return f"{answer_with_link}\n\n추가 정보: {best_add}"
        return answer_with_link
    return None

def handle_request(user_message):
    """명사 추출+유사도 기반: 인사/잡담, 급식, DB 완전일치, 명사/유사도 기반, AI, 폴백"""
    # 급식 관련 키워드가 있으면 실시간 급식 안내
    meal_keywords = ["오늘 급식", "오늘 식단", "오늘 메뉴", "오늘 점심", "오늘 중식"]
    if any(k in user_message for k in meal_keywords):
        return get_meal_info()
    if is_greeting_or_smalltalk(user_message):
        return "안녕하세요! 무엇을 도와드릴까요?"
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT answer, additional_answer FROM qa_data WHERE question = ?', (user_message,))
    result = cursor.fetchone()
    conn.close()
    if result:
        answer, additional_answer = result
        return append_link_to_answer(answer, additional_answer)
    best_link_answer = find_best_link_answer(user_message)
    if best_link_answer:
        return best_link_answer
    print("INFO: AI에게 질문 전달 (DB 컨텍스트 포함)")
    ai_answer = analyze_with_ai(user_message)
    if ai_answer:
        return ai_answer
    return "죄송합니다. 해당 정보를 찾을 수 없습니다. 학교로 문의해 주세요."

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

@app.route('/test')
def test_page():
    """테스트용 HTML 페이지"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>챗봇 스케줄러 테스트</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .button { 
                background: #007bff; color: white; padding: 10px 20px; 
                border: none; border-radius: 5px; cursor: pointer; margin: 5px;
            }
            .button:hover { background: #0056b3; }
            .result { 
                background: #f8f9fa; border: 1px solid #dee2e6; 
                border-radius: 5px; padding: 15px; margin: 10px 0;
                white-space: pre-wrap; font-family: monospace;
            }
            .success { border-color: #28a745; background: #d4edda; }
            .error { border-color: #dc3545; background: #f8d7da; }
        </style>
    </head>
    <body>
        <h1>챗봇 스케줄러 테스트 페이지</h1>
        
        <h2>1. 스케줄러 상태 확인</h2>
        <button class="button" onclick="checkSchedule()">스케줄러 상태 확인</button>
        <div id="scheduleResult" class="result"></div>
        
        <h2>2. DB 상태 확인</h2>
        <button class="button" onclick="checkDB()">DB 상태 확인</button>
        <div id="dbResult" class="result"></div>
        
        <h2>3. 엑셀 데이터 업데이트 테스트</h2>
        <button class="button" onclick="testUpdate()">스케줄러 즉시 실행</button>
        <div id="testResult" class="result"></div>
        
        <h2>4. 수동 업데이트</h2>
        <button class="button" onclick="manualUpdate()">수동 업데이트</button>
        <div id="manualResult" class="result"></div>
        
        <script>
            async function checkSchedule() {
                try {
                    const response = await fetch('/schedule-status');
                    const data = await response.json();
                    document.getElementById('scheduleResult').innerHTML = 
                        JSON.stringify(data, null, 2);
                    document.getElementById('scheduleResult').className = 
                        'result success';
                } catch (error) {
                    document.getElementById('scheduleResult').innerHTML = 
                        '오류: ' + error.message;
                    document.getElementById('scheduleResult').className = 
                        'result error';
                }
            }
            
            async function checkDB() {
                try {
                    const response = await fetch('/db-status');
                    const data = await response.json();
                    document.getElementById('dbResult').innerHTML = 
                        JSON.stringify(data, null, 2);
                    document.getElementById('dbResult').className = 
                        'result success';
                } catch (error) {
                    document.getElementById('dbResult').innerHTML = 
                        '오류: ' + error.message;
                    document.getElementById('dbResult').className = 
                        'result error';
                }
            }
            
            async function testUpdate() {
                try {
                    document.getElementById('testResult').innerHTML = '실행 중...';
                    const response = await fetch('/test-schedule', {method: 'POST'});
                    const data = await response.json();
                    document.getElementById('testResult').innerHTML = 
                        JSON.stringify(data, null, 2);
                    document.getElementById('testResult').className = 
                        'result success';
                } catch (error) {
                    document.getElementById('testResult').innerHTML = 
                        '오류: ' + error.message;
                    document.getElementById('testResult').className = 
                        'result error';
                }
            }
            
            async function manualUpdate() {
                try {
                    document.getElementById('manualResult').innerHTML = '실행 중...';
                    const response = await fetch('/update-excel', {method: 'POST'});
                    const data = await response.json();
                    document.getElementById('manualResult').innerHTML = 
                        JSON.stringify(data, null, 2);
                    document.getElementById('manualResult').className = 
                        'result success';
                } catch (error) {
                    document.getElementById('manualResult').innerHTML = 
                        '오류: ' + error.message;
                    document.getElementById('manualResult').className = 
                        'result error';
                }
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/update-excel', methods=['POST'])
def manual_update_excel():
    """수동으로 엑셀 데이터 업데이트를 실행하는 API"""
    try:
        print(f"[{datetime.now()}] 수동 엑셀 데이터 업데이트 요청됨")
        auto_update_excel_data()
        return jsonify({
            "status": "success",
            "message": "엑셀 데이터 업데이트가 완료되었습니다.",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[{datetime.now()}] 수동 업데이트 중 오류: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"업데이트 중 오류가 발생했습니다: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/schedule-status', methods=['GET'])
def get_schedule_status():
    """스케줄러 상태를 확인하는 API"""
    try:
        jobs = scheduler.get_jobs()
        job_info = []
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return jsonify({
            "status": "success",
            "scheduler_running": scheduler.running,
            "jobs": job_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"스케줄러 상태 확인 중 오류: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test-schedule', methods=['POST'])
def test_schedule():
    """테스트용: 스케줄러를 즉시 실행"""
    try:
        print(f"[{datetime.now()}] 테스트 스케줄러 실행 요청됨")
        
        # 현재 DB 상태 확인
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM qa_data")
        before_count = cursor.fetchone()[0]
        conn.close()
        
        # 스케줄러 실행
        auto_update_excel_data()
        
        # 실행 후 DB 상태 확인
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM qa_data")
        after_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "테스트 스케줄러 실행 완료",
            "before_count": before_count,
            "after_count": after_count,
            "added_count": after_count - before_count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[{datetime.now()}] 테스트 스케줄러 실행 중 오류: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"테스트 실행 중 오류: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/db-status', methods=['GET'])
def get_db_status():
    """DB 상태를 확인하는 API"""
    try:
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        
        # 전체 데이터 수
        cursor.execute("SELECT COUNT(*) FROM qa_data")
        total_count = cursor.fetchone()[0]
        
        # 카테고리별 데이터 수
        cursor.execute("SELECT category, COUNT(*) FROM qa_data GROUP BY category")
        category_counts = dict(cursor.fetchall())
        
        # 최근 추가된 데이터 5개
        cursor.execute("SELECT question, category, created_at FROM qa_data ORDER BY created_at DESC LIMIT 5")
        recent_data = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "total_count": total_count,
            "category_counts": category_counts,
            "recent_data": [
                {
                    "question": row[0][:50] + "..." if len(row[0]) > 50 else row[0],
                    "category": row[1],
                    "created_at": row[2]
                } for row in recent_data
            ],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"DB 상태 확인 중 오류: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 