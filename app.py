from flask import Flask, request, jsonify
import json
import traceback
import sys
from datetime import datetime
from config import PORT, DEBUG, KAKAO_BOT_TOKEN
from ai_logic import AILogic
from database import DatabaseManager

app = Flask(__name__)

# 초기화
ai_logic = AILogic()
db = DatabaseManager()

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
        # 카카오톡 챗봇에서 사용자 ID 추출
        if 'machaao-user-id' in request.headers:
            return request.headers['machaao-user-id']
        elif 'user-id' in request.headers:
            return request.headers['user-id']
        else:
            # 기본값으로 IP 주소 사용
            return request.remote_addr
    except Exception as e:
        exception_handler(e)
        return "unknown_user"

def extract_message(request):
    """요청에서 메시지 추출"""
    try:
        body = request.get_json()
        
        # 카카오톡 챗봇 형식
        if body and 'raw' in body:
            import jwt
            decoded_jwt = jwt.decode(body['raw'], KAKAO_BOT_TOKEN, algorithms=['HS512'])
            text = decoded_jwt['sub']
            if isinstance(text, str):
                text = json.loads(text)
            
            return text['messaging'][0]['message_data']['text']
        
        # 일반 JSON 형식
        elif body and 'message' in body:
            return body['message']
        
        # 폼 데이터
        elif request.form and 'message' in request.form:
            return request.form['message']
        
        else:
            return None
            
    except Exception as e:
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
        success, response = ai_logic.process_message(user_message, user_id)
        
        # 카카오톡 응답 형식 생성
        kakao_response = create_kakao_response(response)
        
        # 퀵 리플라이 추가
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
            
            success, response = ai_logic.process_message(user_message, user_id)
            
            return jsonify({
                "success": success,
                "response": response,
                "user_message": user_message,
                "user_id": user_id
            })
            
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