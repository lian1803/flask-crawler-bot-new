from flask import Flask, request, jsonify
import json
import traceback
import sys
from datetime import datetime
from config import PORT, DEBUG, KAKAO_BOT_TOKEN
from ai_logic import AILogic
from database import DatabaseManager

app = Flask(__name__)

# 지연 초기화를 위한 전역 변수
ai_logic = None
db = None

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
        
        # 카카오톡 챗봇 표준 형식
        if body and 'action' in body and 'params' in body:
            # 카카오톡 챗봇 v2.0 형식
            if 'utterance' in body['action']['params']:
                return body['action']['params']['utterance']
            elif 'message' in body['action']['params']:
                return body['action']['params']['message']
        
        # 카카오톡 챗봇 v1.0 형식
        elif body and 'userRequest' in body:
            return body['userRequest']['utterance']
        
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
            return body['message']
        
        # 폼 데이터
        elif request.form and 'message' in request.form:
            return request.form['message']
        
        print(f"메시지를 찾을 수 없음: {body}")
        return None
            
    except Exception as e:
        print(f"메시지 추출 중 오류: {e}")
        exception_handler(e)
        return None

def create_kakao_response(message):
    """카카오톡 응답 형식 생성"""
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

def create_quick_replies():
    """퀵 리플라이 버튼 생성"""
    return [
        {
            "action": "message",
            "label": "오늘 급식",
            "messageText": "오늘 급식 메뉴 알려줘"
        },
        {
            "action": "message", 
            "label": "공지사항",
            "messageText": "최신 공지사항 알려줘"
        },
        {
            "action": "message",
            "label": "도움말",
            "messageText": "무엇을 도와드릴까요?"
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
        # 사용자 ID와 메시지 추출
        user_id = extract_user_id(request)
        user_message = extract_message(request)
        
        if not user_message:
            return jsonify({"error": "메시지를 찾을 수 없습니다."}), 400
        
        print(f"사용자 {user_id}: {user_message}")
        
        # AI 로직으로 메시지 처리
        ai_logic = get_ai_logic()
        success, response = ai_logic.process_message(user_message, user_id)
        
        # 응답 타입에 따른 카카오톡 응답 형식 생성
        if isinstance(response, dict) and response.get("type") == "image":
            # 이미지 응답
            kakao_response = {
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleImage": {
                                "imageUrl": response["imageUrl"],
                                "altText": response["altText"]
                            }
                        },
                        {
                            "simpleText": {
                                "text": response["text"],
                                "quickReplies": create_quick_replies()
                            }
                        }
                    ]
                }
            }
        else:
            # 텍스트 응답
            if isinstance(response, dict):
                text = response.get("text", str(response))
            else:
                text = str(response)
            
            kakao_response = create_kakao_response(text)
            kakao_response["template"]["outputs"][0]["simpleText"]["quickReplies"] = create_quick_replies()
        
        return jsonify(kakao_response)
        
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        exception_handler(e)
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
            
            # 응답 타입에 따른 처리
            if isinstance(response, dict) and response.get("type") == "image":
                response_data = {
                    "success": success,
                    "response_type": "image",
                    "image_url": response["imageUrl"],
                    "alt_text": response["altText"],
                    "text": response["text"],
                    "user_message": user_message,
                    "user_id": user_id
                }
            else:
                response_data = {
                    "success": success,
                    "response_type": "text",
                    "response": response,
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

if __name__ == '__main__':
    print(f"와석초등학교 챗봇 서버 시작 - 포트: {PORT}")
    print(f"디버그 모드: {DEBUG}")
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG) 