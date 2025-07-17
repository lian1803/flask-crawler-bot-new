from flask import Flask, request, jsonify
import json
import traceback
import sys
import os
import subprocess
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import PORT, DEBUG, KAKAO_BOT_TOKEN
from ai_logic import AILogic
from database import DatabaseManager

app = Flask(__name__)

# 지연 초기화를 위한 전역 변수
ai_logic = None
db = None

# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.start()

def get_ai_logic():
    """AI 로직 인스턴스 가져오기 (지연 초기화)"""
    global ai_logic
    if ai_logic is None:
        ai_logic = AILogic()
    return ai_logic

def get_db():
    """DB 인스턴스 가져오기 (지연 초기화)"""
    global db
    if db is None:
        db = DatabaseManager()
    return db

def run_crawler():
    """크롤러 실행 함수"""
    try:
        print("🔄 자동 크롤링 시작...")
        result = subprocess.run(['python', 'incremental_notice_crawler.py'], 
                              capture_output=True, text=True, timeout=300)
        print(f"크롤링 결과: {result.stdout}")
        if result.stderr:
            print(f"크롤링 오류: {result.stderr}")
        
        # 크롤링 후 GitHub에 자동 커밋
        commit_to_github()
        
    except Exception as e:
        print(f"크롤링 실행 오류: {e}")

def commit_to_github():
    """GitHub에 자동 커밋"""
    try:
        print("📝 GitHub 자동 커밋 시작...")
        
        # Git 상태 확인
        subprocess.run(['git', 'add', '.'], check=True)
        
        # 변경사항이 있는지 확인
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            # 변경사항이 있으면 커밋
            commit_message = f"자동 크롤링 업데이트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            subprocess.run(['git', 'push'], check=True)
            print(f"✅ GitHub 커밋 완료: {commit_message}")
        else:
            print("📝 변경사항이 없어 커밋을 건너뜁니다.")
            
    except Exception as e:
        print(f"GitHub 커밋 오류: {e}")

def setup_scheduler():
    """스케줄러 설정"""
    # 매일 오전 6시에 크롤링 실행
    scheduler.add_job(
        func=run_crawler,
        trigger=CronTrigger(hour=6, minute=0),
        id='daily_crawler',
        name='매일 자동 크롤링',
        replace_existing=True
    )
    print("⏰ 자동 크롤링 스케줄러 설정 완료 (매일 오전 6시)")

def exception_handler(exception):
    """예외 처리 함수"""
    caller = sys._getframe(1).f_code.co_name
    print(f"{caller} 함수에서 오류 발생")
    if hasattr(exception, "message"):
        print(exception.message)
    else:
        print("예상치 못한 오류: ", sys.exc_info()[0])

def extract_user_id(request):
    """요청에서 사용자 ID 추출"""
    try:
        body = request.get_json()
        
        # 카카오톡 챗봇 표준 형식
        if body and 'userRequest' in body:
            return body['userRequest']['user']['id']
        elif body and 'action' in body and 'params' in body:
            return body['action']['params'].get('userId', 'unknown')
        
        # machaao 형식
        if 'machaao-user-id' in request.headers:
            return request.headers['machaao-user-id']
        elif 'user-id' in request.headers:
            return request.headers['user-id']
        
        # 기본값으로 IP 주소 사용
        return request.remote_addr
    except Exception as e:
        exception_handler(e)
        return "unknown_user"

def extract_message(request):
    """요청에서 메시지 추출"""
    try:
        body = request.get_json()
        print(f"받은 요청 데이터: {body}")
        
        # 카카오톡 챗봇 v1.0 형식 (실제 카카오톡 챗봇 빌더 형식)
        if body and 'userRequest' in body:
            print(f"userRequest 내용: {body['userRequest']}")
            if 'utterance' in body['userRequest']:
                utterance = body['userRequest']['utterance']
                print(f"userRequest.utterance 추출: {utterance}")
                return utterance
            else:
                print("userRequest에 utterance가 없습니다")
        
        # 카카오톡 챗봇 빌더 테스트 형식
        elif body and 'action' in body and 'params' in body['action']:
            print(f"action.params 내용: {body['action']['params']}")
            # 카카오톡 챗봇 v2.0 형식
            if 'utterance' in body['action']['params']:
                utterance = body['action']['params']['utterance']
                print(f"utterance 추출: {utterance}")
                return utterance
            elif 'message' in body['action']['params']:
                message = body['action']['params']['message']
                print(f"message 추출: {message}")
                return message
        
        # machaao 형식
        elif body and 'raw' in body:
            try:
                import jwt
                decoded_jwt = jwt.decode(body['raw'], KAKAO_BOT_TOKEN, algorithms=['HS512'])
                text = decoded_jwt['sub']
                if isinstance(text, str):
                    text = json.loads(text)
                return text['messaging'][0]['message_data']['text']
            except:
                pass
        
        # 일반 JSON 형식
        elif body and 'message' in body:
            message = body['message']
            print(f"body.message 추출: {message}")
            return message
        
        # 폼 데이터
        elif request.form and 'message' in request.form:
            message = request.form['message']
            print(f"form.message 추출: {message}")
            return message
        
        print(f"메시지를 찾을 수 없음: {body}")
        return None
            
    except Exception as e:
        print(f"메시지 추출 중 오류: {e}")
        exception_handler(e)
        return None

def create_kakao_response(message, quick_replies=None):
    """카카오톡 응답 형식 생성"""
    # 메시지가 None이거나 빈 문자열인 경우 기본 메시지 사용
    if not message or message.strip() == "":
        message = "안녕하세요! 와석초등학교 챗봇입니다."
    
    # 메시지 길이 제한 (카카오톡 제한)
    if len(message) > 1000:
        message = message[:997] + "..."
    
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": str(message)
                    }
                }
            ]
        }
    }

    # QuickReplies가 있으면 추가 (최대 10개)
    if quick_replies and isinstance(quick_replies, list):
        if len(quick_replies) > 10:
            quick_replies = quick_replies[:10]
        response["template"]["quickReplies"] = quick_replies
    
    return response

def create_quick_replies(category=None):
    """퀵 리플라이 버튼 생성 (단계별)"""
    
    # 메인 카테고리 (첫 단계) - 유치원/초등학교 구분
    if category is None:
        return [
            {
                "action": "message",
                "label": "👶 유치원",
                "messageText": "유치원"
            },
            {
                "action": "message",
                "label": "🏫 초등학교",
                "messageText": "초등학교"
            }
        ]
    
    # 유치원 메뉴
    elif category == "유치원":
        return [
            {
                "action": "message",
                "label": "📅 학사일정",
                "messageText": "유치원 학사일정"
            },
            {
                "action": "message",
                "label": "⏰ 운영시간",
                "messageText": "유치원 운영시간"
            },
            {
                "action": "message",
                "label": "🎨 방과후",
                "messageText": "유치원 방과후"
            },
            {
                "action": "📞 상담/문의",
                "messageText": "유치원 상담문의"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "메인메뉴"
            }
        ]
    
    # 초등학교 메뉴
    elif category == "초등학교":
        return [
            {
                "action": "message",
                "label": "📅 학사일정",
                "messageText": "학사일정"
            },
            {
                "action": "message",
                "label": "🍽️ 급식정보",
                "messageText": "급식정보"
            },
            {
                "action": "message",
                "label": "🎨 방과후",
                "messageText": "방과후"
            },
            {
                "action": "message",
                "label": "📞 상담/문의",
                "messageText": "상담문의"
            },
            {
                "action": "message",
                "label": "📋 더보기",
                "messageText": "더보기"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "메인메뉴"
            }
        ]
    
    # 유치원 학사일정 세부 카테고리
    elif category == "유치원 학사일정":
        return [
            {
                "action": "message",
                "label": "🏫 개학일",
                "messageText": "유치원 개학일"
            },
            {
                "action": "message",
                "label": "🏖️ 방학일",
                "messageText": "유치원 방학일"
            },
            {
                "action": "message",
                "label": "🎓 졸업식",
                "messageText": "유치원 졸업식"
            },
            {
                "action": "message",
                "label": "🎉 행사일",
                "messageText": "유치원 행사일"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "유치원"
            }
        ]
    
    # 유치원 운영시간 세부 카테고리
    elif category == "유치원 운영시간":
        return [
            {
                "action": "message",
                "label": "⏰ 교육과정",
                "messageText": "유치원 교육과정 시간"
            },
            {
                "action": "message",
                "label": "🎨 방과후과정",
                "messageText": "유치원 방과후과정 시간"
            },
            {
                "action": "message",
                "label": "👨‍🏫 교사면담",
                "messageText": "유치원 교사면담 시간"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "유치원"
            }
        ]
    
    # 유치원 방과후 세부 카테고리
    elif category == "유치원 방과후":
        return [
            {
                "action": "message",
                "label": "🎨 특성화",
                "messageText": "유치원 특성화"
            },
            {
                "action": "message",
                "label": "💰 교육비",
                "messageText": "유치원 교육비"
            },
            {
                "action": "message",
                "label": "📝 신청방법",
                "messageText": "유치원 방과후 신청방법"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "유치원"
            }
        ]
    
    # 유치원 상담문의 세부 카테고리
    elif category == "유치원 상담문의":
        return [
            {
                "action": "message",
                "label": "👨‍🏫 담임상담",
                "messageText": "유치원 담임상담"
            },
            {
                "action": "message",
                "label": "📞 전화번호",
                "messageText": "유치원 전화번호"
            },
            {
                "action": "message",
                "label": "🔄 입학문의",
                "messageText": "유치원 입학문의"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "유치원"
            }
        ]
    
    # 학사일정 세부 카테고리 (초등학교)
    elif category == "학사일정":
        return [
            {
                "action": "message",
                "label": "🏫 개학일",
                "messageText": "개학일"
            },
            {
                "action": "message",
                "label": "🏖️ 방학일",
                "messageText": "방학일"
            },
            {
                "action": "message",
                "label": "📝 시험일",
                "messageText": "시험일"
            },
            {
                "action": "message",
                "label": "🎉 행사일",
                "messageText": "행사일"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "초등학교"
            }
        ]
    
    # 급식정보 세부 카테고리 (초등학교)
    elif category == "급식정보":
        return [
            {
                "action": "message",
                "label": "🍽️ 오늘 급식",
                "messageText": "오늘 급식 메뉴 알려줘"
            },
            {
                "action": "message", 
                "label": "📅 이번주 급식",
                "messageText": "이번주 급식 메뉴 알려줘"
            },
            {
                "action": "message",
                "label": "❓ 급식 문의",
                "messageText": "급식 관련 문의"
            },
            {
                "action": "message",
                "label": "🍎 알레르기 정보",
                "messageText": "급식 알레르기 정보"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "초등학교"
            }
        ]
    
    # 방과후 세부 카테고리 (초등학교)
    elif category == "방과후":
        return [
            {
                "action": "message",
                "label": "🏠 늘봄교실",
                "messageText": "늘봄교실"
            },
            {
                "action": "message",
                "label": "🎨 방과후학교",
                "messageText": "방과후학교"
            },
            {
                "action": "message",
                "label": "📝 신청방법",
                "messageText": "방과후 신청방법"
            },
            {
                "action": "message",
                "label": "⏰ 운영시간",
                "messageText": "방과후 운영시간"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "초등학교"
            }
        ]
    
    # 상담/문의 세부 카테고리 (초등학교)
    elif category == "상담문의":
        return [
            {
                "action": "message",
                "label": "👨‍🏫 담임상담",
                "messageText": "담임선생님 상담"
            },
            {
                "action": "message",
                "label": "📞 전화번호",
                "messageText": "학교 전화번호"
            },
            {
                "action": "message",
                "label": "🔄 전학문의",
                "messageText": "전학 문의"
            },
            {
                "action": "message",
                "label": "📋 서류발급",
                "messageText": "서류 발급 문의"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "초등학교"
            }
        ]
    
    # 더보기 세부 카테고리 (초등학교)
    elif category == "더보기":
        return [
            {
                "action": "message",
                "label": "🏢 학교시설",
                "messageText": "학교시설"
            },
            {
                "action": "message",
                "label": "🚌 등하교",
                "messageText": "등하교"
            },
            {
                "action": "message",
                "label": "👶 유치원",
                "messageText": "유치원"
            },
            {
                "action": "message",
                "label": "🏥 보건실",
                "messageText": "보건실"
            },
            {
                "action": "message",
                "label": "⬅️ 뒤로가기",
                "messageText": "초등학교"
            }
        ]
    
    # 기본 (메인으로 돌아가기)
    else:
        return [
            {
                "action": "message",
                "label": "🏠 메인메뉴",
                "messageText": "메인메뉴"
            }
        ]

@app.route('/', methods=['GET'])
def root():
    """루트 엔드포인트"""
    return jsonify({
        "status": "ok",
        "message": "와석초등학교 챗봇 서버가 정상 작동 중입니다.",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """카카오톡 웹훅 엔드포인트"""
    try:
        # 요청 데이터 로깅
        print("=== 웹훅 요청 받음 ===")
        print(f"Headers: {dict(request.headers)}")
        print(f"Body: {request.get_data(as_text=True)}")
        
        # 사용자 ID와 메시지 추출
        user_id = extract_user_id(request)
        user_message = extract_message(request)
        
        print(f"추출된 사용자 ID: {user_id}")
        print(f"추출된 메시지: {user_message}")
        
        if not user_message:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleText": {
                                "text": "메시지를 이해하지 못했습니다. 다시 말씀해 주세요."
                            }
                        }
                    ]
                }
            })
        
        print(f"사용자 {user_id}: {user_message}")
        
        # AI 로직으로 메시지 처리 (타임아웃 방지)
        try:
            ai_logic = get_ai_logic()
            success, response = ai_logic.process_message(user_message, user_id)
            
            # 텍스트 응답으로 통일
            if isinstance(response, dict):
                text = response.get("text", str(response))
            else:
                text = str(response)
                
        except Exception as ai_error:
            print(f"AI 로직 오류: {ai_error}")
            text = "안녕하세요! 와석초등학교 챗봇입니다. 무엇을 도와드릴까요?"
        
        # 사용자 메시지에 따른 QuickReplies 결정
        quick_replies_category = None
        
        # 메인 카테고리 키워드 확인 (유치원/초등학교 구분 포함)
        if user_message in ["유치원", "초등학교", "학사일정", "급식정보", "방과후", "상담문의", "더보기", "메인메뉴"]:
            if user_message == "메인메뉴":
                quick_replies_category = None  # 메인 메뉴
            else:
                quick_replies_category = user_message
        
        # 유치원 세부 카테고리 확인
        elif user_message in ["유치원 학사일정", "유치원 운영시간", "유치원 방과후", "유치원 상담문의"]:
            quick_replies_category = user_message
        
        # 초등학교 세부 카테고리 확인
        elif user_message in ["학사일정", "급식정보", "방과후", "상담문의", "더보기"]:
            quick_replies_category = user_message
        
        # 특별한 응답 메시지들 (QuickReplies 없이)
        special_responses = [
            # 초등학교 관련
            "오늘 급식 메뉴 알려줘", "이번주 급식 메뉴 알려줘", "급식 관련 문의", 
            "급식 알레르기 정보", "개학일", "방학일", "시험일", "행사일",
            "늘봄교실", "방과후학교", "방과후 신청방법", "방과후 운영시간",
            "담임선생님 상담", "학교 전화번호", "전학 문의", "서류 발급 문의",
            "학교시설", "등하교", "보건실",
            # 유치원 관련
            "유치원 개학일", "유치원 방학일", "유치원 졸업식", "유치원 행사일",
            "유치원 교육과정 시간", "유치원 방과후과정 시간", "유치원 교사면담 시간",
            "유치원 특성화", "유치원 교육비", "유치원 방과후 신청방법",
            "유치원 담임상담", "유치원 전화번호", "유치원 입학문의"
        ]
        
        # 특별한 응답인 경우 QuickReplies 없이
        if any(keyword in user_message for keyword in special_responses):
            kakao_response = create_kakao_response(text)
        # 첫 인사나 일반적인 질문인 경우 메인 메뉴 제공
        elif any(keyword in user_message for keyword in ["안녕", "안녕하세요", "안녕!", "안녕~", "도움", "도움말", "무엇을", "뭐해", "뭐하고 있어"]):
            kakao_response = create_kakao_response(text, create_quick_replies(None))  # 메인 메뉴
        else:
            kakao_response = create_kakao_response(text, create_quick_replies(quick_replies_category))
        
        # 응답 로깅
        print(f"응답 데이터: {kakao_response}")
        
        # 응답 형식 검증
        if not isinstance(kakao_response, dict):
            raise ValueError("응답이 딕셔너리 형식이 아닙니다")
        
        if "version" not in kakao_response:
            kakao_response["version"] = "2.0"
        
        if "template" not in kakao_response:
            raise ValueError("template 필드가 없습니다")
        
        return jsonify(kakao_response)
        
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        exception_handler(e)
        print(f"오류 발생: {e}")
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "죄송합니다. 서비스에 일시적인 문제가 발생했습니다."
                        }
                    }
                ]
            }
        })

@app.route('/test', methods=['GET', 'POST'])
def test():
    """테스트 엔드포인트"""
    if request.method == 'GET':
        return jsonify({
            "status": "test",
            "message": "테스트 페이지입니다. POST로 메시지를 보내보세요.",
            "example": {
                "message": "오늘 급식 메뉴 알려줘"
            }
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            user_message = data.get('message', '안녕하세요')
            user_id = data.get('user_id', 'test_user')
            
            print(f"테스트 - 사용자 {user_id}: {user_message}")
            
            ai_logic = get_ai_logic()
            success, response = ai_logic.process_message(user_message, user_id)
            
            # 텍스트 응답으로 통일
            if isinstance(response, dict):
                response_text = response.get("text", str(response))
            else:
                response_text = str(response)
            
            response_data = {
                "success": success,
                "response_type": "text",
                "response": response_text,
                "user_message": user_message,
                "user_id": user_id
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            exception_handler(e)
            return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "disconnected"
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """통계 정보 엔드포인트"""
    try:
        # QA 데이터 개수
        qa_count = len(db.get_qa_data())
        
        # 최근 대화 히스토리 개수 (테스트용)
        test_history = db.get_conversation_history("test_user", limit=10)
        
        return jsonify({
            "qa_data_count": qa_count,
            "recent_conversations": len(test_history),
            "server_status": "running",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        exception_handler(e)
        return jsonify({"error": str(e)}), 500

@app.route('/crawl', methods=['POST'])
def manual_crawl():
    """수동 크롤링 실행 엔드포인트"""
    try:
        print("🔄 수동 크롤링 요청 받음")
        run_crawler()
        return jsonify({
            "status": "success",
            "message": "크롤링이 성공적으로 실행되었습니다.",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        exception_handler(e)
        return jsonify({"error": str(e)}), 500

@app.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """스케줄러 상태 확인 엔드포인트"""
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
            "scheduler_running": scheduler.running,
            "jobs": job_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        exception_handler(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"와석초등학교 챗봇 서버 시작 - 포트: {PORT}")
    print(f"디버그 모드: {DEBUG}")
    
    # 스케줄러 설정
    setup_scheduler()
    
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG) 